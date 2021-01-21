from tqdm import tqdm

from .core import OSFCore
from ..exceptions import FolderExistsException
from io import BytesIO


def copyfileobj(fsrc, fdst, total, length=16*1024):
    """Copy data from file-like object fsrc to file-like object fdst

    This is like shutil.copyfileobj but with a progressbar.
    """
    with tqdm(unit='bytes', total=total, unit_scale=True) as pbar:
        while 1:
            buf = fsrc.read(length)
            if not buf:
                break
            fdst.write(buf)
            pbar.update(len(buf))


class File(OSFCore):
    def _update_attributes(self, file):
        if not file:
            return

        self.id = self._get_attribute(file, 'id')

        self._endpoint = self._get_attribute(file, 'links', 'self')
        self._upload_url = self._get_attribute(file, 'links', 'upload')
        self._download_url = self._upload_url
        self._html_url = self._get_attribute(file, 'links', 'html')
        self._delete_url = self._get_attribute(file, 'links', 'delete')
        self.osf_path = self._get_attribute(file, 'attributes', 'path')
        self.path = self._get_attribute(file,
                                        'attributes', 'materialized_path')
        self.name = self._get_attribute(file, 'attributes', 'name')
        self.date_created = self._get_attribute(file,
                                                'attributes', 'date_created')
        self.date_modified = self._get_attribute(file,
                                                 'attributes', 'date_modified')
        self.hashes = self._get_attribute(file,
                                          'attributes', 'extra', 'hashes')
        self.size = self._get_attribute(file, 'attributes', 'size')

    def __str__(self):
        return '<File [{0}, {1}]>'.format(self.id, self.path)

    def write_to(self, fp):
        """Write contents of this file to a local file.

        Pass in a filepointer `fp` that has been opened for writing in
        binary mode.
        """
        if 'b' not in getattr(fp, "mode", "") and not isinstance(fp, BytesIO):
            raise ValueError("File has to be opened in binary mode.")

        response = self._get(self._download_url, stream=True)
        if response.status_code == 200:
            response.raw.decode_content = True
            copyfileobj(response.raw, fp,
                        int(response.headers['Content-Length']))

        else:
            raise RuntimeError("Response has status "
                               "code {}.".format(response.status_code))

    def remove(self):
        """Remove this file from the remote storage."""
        response = self._delete(self._delete_url)
        if response.status_code != 204:
            raise RuntimeError('Could not delete {}.'.format(self.path))

    def update(self, fp):
        """Update the remote file from a local file.

        Pass in a filepointer `fp` that has been opened for writing in
        binary mode.
        """
        if 'b' not in getattr(fp, "mode", "") and not isinstance(fp, BytesIO):
            raise ValueError("File has to be opened in binary mode.")

        url = self._upload_url
        # peek at the file to check if it is an ampty file which needs special
        # handling in requests. If we pass a file like object to data that
        # turns out to be of length zero then no file is created on the OSF
        if fp.read(1):
            response = self._put(url, data=fp)
        else:
            response = self._put(url, data=b'')

        if response.status_code != 200:
            msg = ('Could not update {} (status '
                   'code: {}).'.format(self.path, response.status_code))
            raise RuntimeError(msg)


class ContainerMixin:
    def _iter_children(self, url, kind, klass, recurse=None):
        """Iterate over all children of `kind`

        Yield an instance of `klass` when a child is of type `kind`. Uses
        `recurse` as the path of attributes in the JSON returned from `url`
        to find more children.
        """
        children = self._follow_next(url)

        while children:
            child = children.pop()
            kind_ = child['attributes']['kind']
            if kind_ == kind:
                yield klass(child, self.session)
            elif recurse is not None:
                # recurse into a child and add entries to `children`
                url = self._get_attribute(child, *recurse)
                children.extend(self._follow_next(url))

    @property
    def files(self):
        """Iterate over all files in this folder.

        Unlike a `Storage` instance this does not recursively find all files.
        Only lists files in this folder.
        """
        return self._iter_children(self._files_url, 'file', File)

    @property
    def folders(self):
        """Iterate over top-level folders in this folder."""
        return self._iter_children(self._files_url, 'folder', Folder)

    def create_folder(self, name, exist_ok=False):
        url = self._new_folder_url
        # Create a new sub-folder
        response = self._put(url, params={'name': name})
        if response.status_code == 409 and not exist_ok:
            raise FolderExistsException(name)

        elif response.status_code == 409 and exist_ok:
            for folder in self.folders:
                if folder.name == name:
                    return folder

        elif response.status_code == 201:
            return _WaterButlerFolder(response.json()['data'], self.session)

        else:
            raise RuntimeError("Response has status code {} while creating "
                               "folder {}.".format(response.status_code,
                                                   name))


class Folder(OSFCore, ContainerMixin):
    def _update_attributes(self, file):
        if not file:
            return

        self.id = self._get_attribute(file, 'id')

        self._endpoint = self._get_attribute(file, 'links', 'self')

        self._delete_url = self._get_attribute(file, 'links', 'delete')
        self._new_folder_url = self._get_attribute(file, 'links', 'new_folder')
        self._new_file_url = self._get_attribute(file, 'links', 'upload')
        self._move_url = self._get_attribute(file, 'links', 'move')

        self._files_key = ('relationships', 'files', 'links', 'related',
                           'href')
        self._files_url = self._get_attribute(file, *self._files_key)

        self.osf_path = self._get_attribute(file, 'attributes', 'path')
        self.path = self._get_attribute(file,
                                        'attributes', 'materialized_path')
        self.name = self._get_attribute(file, 'attributes', 'name')
        self.date_created = self._get_attribute(file,
                                                'attributes', 'date_created')
        self.date_modified = self._get_attribute(file,
                                                 'attributes', 'date_modified')

    def __str__(self):
        return '<Folder [{0}, {1}]>'.format(self.id, self.path)


class _WaterButlerFolder(OSFCore, ContainerMixin):
    """A slimmed down `Folder` built from a WaterButler response

    This representation is enough to navigate the folder structure
    and create new, rename and delete sub-folders.

    Users should never see this, always show them a full `Folder`.
    """
    def __str__(self):
        return '<_WaterButlerFolder [{0}]>'.format(self.id)

    def _update_attributes(self, file):
        if not file:
            return

        self.id = self._get_attribute(file, 'id')

        self.osf_path = self._get_attribute(file, 'attributes', 'path')

        self._delete_url = self._get_attribute(file, 'links', 'delete')
        self._new_folder_url = self._get_attribute(file, 'links', 'new_folder')
        self._new_file_url = self._get_attribute(file, 'links', 'upload')
        self._move_url = self._get_attribute(file, 'links', 'move')

    @property
    def full_folder(self):
        base_url = "https://api.osf.io/v2/files"
        folder = self._json(self._get(base_url % self.osf_path), 200)
        return Folder(folder, self.session)
