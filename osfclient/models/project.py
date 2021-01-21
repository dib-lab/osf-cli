from .core import OSFCore
from .storage import Storage
from json import dumps

import logging

logger = logging.getLogger()

osf_to_jsonld = {
    "title": "https://schema.org/title",
    "description": "https://schema.org/description",
    "category": "https://schema.org/category",
    "tags": "https://schema.org/keywords",
    "public": "https://schema.org/publicAccess",
    "date_created": "https://schema.org/dateCreated",
    "date_modified": "https://schema.org/dateModified",
    "id": "https://schema.org/identifier",
    "self": "https://schema.org/url",
    "storages_url": "https://schema.org/downloadUrl",
}


class Project(OSFCore):
    _types = ["nodes", "registrations"]

    def __init__(self, json, session=None, address=None):
        try:
            data = self.__transform_from_jsonld(json)
        except Exception as e:
            data = json

        super().__init__(data, session=session, address=address)

    def __transform_from_jsonld(self, json):
        inverse_transform = {value: key for key, value in osf_to_jsonld.items()}
        data = {
            "data": {
                "attributes": {
                    inverse_transform[key]: value
                    for key, value in json.items()
                    if key in inverse_transform
                },
                "links": {"self": json[osf_to_jsonld["self"]]},
                "id": json[osf_to_jsonld["id"]],
                "relationships": {
                    "files": {
                        "links": {
                            "related": {"href": json[osf_to_jsonld["storages_url"]]}
                        }
                    }
                },
            }
        }
        return data

    def _update_attributes(self, project):
        logger.debug("got project to update: {}".format(project))

        if not project:
            return

        try:
            project = self.__transform_from_jsonld(project)
        except KeyError:
            pass

        try:
            project = project["data"]
        except Exception as e:
            pass

        try:
            for key, value in project["attributes"].items():
                setattr(self, key, value)
                logger.debug("set {}: {}".format(key, value))
        except Exception as e:
            logger.error(e, exc_info=True)

        try:
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

        except Exception as e:
            logger.error(e, exc_info=True)

    def __str__(self):
        return "<Project [{0}]>".format(self.id)

    def metadata(self, only_mutable=False, jsonld=False):
        """Returns all metadata for this project.

        Args:
            only_mutable (bool, optional): If True, returns only the mutables. Otherwise all metadata. Defaults to False.
            jsonld (bool, optional): If true, returns a jsonld object. Otherwise OSF specific key names.
        """

        data = {
            key: value for key, value in self.__dict__.items() if key in osf_to_jsonld
        }

        if only_mutable:
            return {
                key: value
                for key, value in data.items()
                if key not in "id" and "date_" not in key and value
            }

        # jsonld exporter
        if jsonld:
            data = {osf_to_jsonld[key]: value for key, value in data.items()}

            data[osf_to_jsonld["self"]] = self._endpoint
            data[osf_to_jsonld["storages_url"]] = self._storages_url

        return data

    def update(self, json=None):
        """Updates the mutable attributes on OSF.


        Args:
            json (dict, optional): Set this parameter, if you want to update attributes on local and OSF servers in one step.

        Returns:
            [boolean]: True, when updates success. Otherwise False.
        """

        if json is not None:
            self._update_attributes(json)

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

        logger.debug("send {}".format(data))

        try:
            data = self._json(self._put(url, data=data), 200)
            self._update_attributes(data)
            return True
        except RuntimeError:
            raise
            return False

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

    def list_doi(self, category="doi"):
        """List all unique identifier."""
        type_ = "nodes"
        url = self._build_url(type_, self.id, "identifiers")

        data = self._json(self._get(url), 200)
        data = data["data"][0]
        identifier = self._get_attribute(data, "attributes", "value")

        return identifier

    def create_doi(self, category="doi"):
        """Create a unique identifier."""
        type_ = "nodes"
        url = self._build_url(type_, self.id, "identifiers")

        data = dumps(
            {"data": {"type": "identifiers", "attributes": {"category": category}}}
        )

        data = self._json(self._post(url, data=data), 201)
        data = data["data"][0]
        identifier = self._get_attribute(data, "attributes", "value")

        return identifier
