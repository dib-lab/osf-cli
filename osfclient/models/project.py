from .core import OSFCore
from .storage import Storage
from json import dumps


class Project(OSFCore):
    _types = ["nodes", "registrations"]

    def _update_attributes(self, project):
        if not project:
            return

        project = project["data"]
        self._endpoint = self._get_attribute(project, "links", "self")
        self.id = self._get_attribute(project, "id")
        attrs = self._get_attribute(project, "attributes")
        self.title = self._get_attribute(attrs, "title")
        self.date_created = self._get_attribute(attrs, "date_created")
        self.date_modified = self._get_attribute(attrs, "date_modified")
        self.description = self._get_attribute(attrs, "description")
        self.category = self._get_attribute(attrs, "category")
        self.tags = self._get_attribute(attrs, "tags")
        self.public = self._get_attribute(attrs, "public")

        storages = ["relationships", "files", "links", "related", "href"]
        self._storages_url = self._get_attribute(project, *storages)

    def __str__(self):
        return "<Project [{0}]>".format(self.id)

    def metadata(self, only_mutable=False, jsonld=False):
        """Returns all metadata for this project.

        Args:
            only_mutable (bool, optional): If True, returns only the mutables. Otherwise all metadata. Defaults to False.
            jsonld (bool, optional): If true, returns a jsonld object. Otherwise OSF specific key names.
        """
        data = self.__dict__

        if only_mutable:
            mutables = ["title", "description", "category", "tags", "public"]
            data = {key: value for key, value in data.items() if key in mutables}

        if jsonld:
            transform_mutables = {
                "title": "https://schema.org/title",
                "description": "https://schema.org/description",
                "category": "https://schema.org/category",
                "tags": "https://schema.org/keywords",
                "public": "https://schema.org/publicAccess",
            }
            data = {
                transform_mutables[key]: value
                for key, value in data.items()
                if key in transform_mutables
            }

        return data

    def update(self):
        """Updates the mutable attributes on OSF.

        Returns:
            [boolean]: True, when updates success. Otherwise False.
        """
        type_ = self._guid(self.id)
        url = self._build_url(type_, self.id)

        data = dumps(
            {
                "data": {
                    "type": type_,
                    "id": self.id,
                    "attributes": self.metadata(only_mutable=True),
                }
            }
        )
        return self._put(url, data=data).status_code < 300

    def delete(self):
        type_ = self._guid(self.id)
        url = self._build_url(type_, self.id)

        return self._delete(url).status_code < 300

    def storage(self, provider="osfstorage"):
        """Return storage `provider`."""
        stores = self._json(self._get(self._storages_url), 200)
        stores = stores["data"]
        for store in stores:
            provides = self._get_attribute(store, "attributes", "provider")
            if provides == provider:
                return Storage(store, self.session)

        raise RuntimeError("Project has no storage " "provider '{}'".format(provider))

    @property
    def storages(self):
        """Iterate over all storages for this projects."""
        stores = self._json(self._get(self._storages_url), 200)
        stores = stores["data"]
        for store in stores:
            yield Storage(store, self.session)
