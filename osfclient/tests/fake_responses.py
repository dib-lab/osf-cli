import json
from osfclient.models import osf_to_jsonld

# Use this to initialize a `Project` instance
node_json = """
{
  "data": {
    "relationships": {
      "files": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/files/",
            "meta": {}
          }
        }
      },
      "view_only_links": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/view_only_links/",
            "meta": {}
          }
        }
      },
      "citation": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/citation/",
            "meta": {}
          }
        }
      },
      "license": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/licenses/563c1ffbda3e240129e72c03/",
            "meta": {}
          }
        }
      },
      "contributors": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/contributors/",
            "meta": {}
          }
        }
      },
      "forks": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/forks/",
            "meta": {}
          }
        }
      },
      "root": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/",
            "meta": {}
          }
        }
      },
      "identifiers": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/identifiers/",
            "meta": {}
          }
        }
      },
      "comments": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/comments/?filter%5Btarget%5D=f3szh",
            "meta": {}
          }
        }
      },
      "registrations": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/registrations/",
            "meta": {}
          }
        }
      },
      "logs": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/logs/",
            "meta": {}
          }
        }
      },
      "node_links": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/node_links/",
            "meta": {}
          }
        }
      },
      "linked_nodes": {
        "links": {
          "self": {
            "href": "https://api.osf.io/v2/nodes/f3szh/relationships/linked_nodes/",
            "meta": {}
          },
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/linked_nodes/",
            "meta": {}
          }
        }
      },
      "wikis": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/wikis/",
            "meta": {}
          }
        }
      },
      "affiliated_institutions": {
        "links": {
          "self": {
            "href": "https://api.osf.io/v2/nodes/f3szh/relationships/institutions/",
            "meta": {}
          },
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/institutions/",
            "meta": {}
          }
        }
      },
      "children": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/children/",
            "meta": {}
          }
        }
      },
      "preprints": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/preprints/",
            "meta": {}
          }
        }
      },
      "draft_registrations": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/nodes/f3szh/draft_registrations/",
            "meta": {}
          }
        }
      }
    },
    "links": {
      "self": "https://api.osf.io/v2/nodes/f3szh/",
      "html": "https://osf.io/f3szh/"
    },
    "attributes": {
      "category": "project",
      "fork": false,
      "preprint": true,
      "description": "this is a test for preprint citations",
      "current_user_permissions": [
        "read"
      ],
      "date_modified": "2017-03-17T16:11:35.721000",
      "title": "Preprint Citations Test",
      "collection": false,
      "registration": false,
      "date_created": "2017-03-17T16:09:14.864000",
      "current_user_can_comment": false,
      "node_license": {
        "copyright_holders": [],
        "year": "2017"
      },
      "public": true,
      "tags": [
        "qatest"
      ]
    },
    "type": "{type}",
    "id": "f3szh"
  }
}
"""


def _make_jsonld():
    node = _build_node("nodes")

    data = {
        osf_to_jsonld[key]: value
        for key, value in node["data"]["attributes"].items()
        if key in osf_to_jsonld.keys()
    }

    data.update(
        {
            osf_to_jsonld["id"]: node["data"]["id"],
            osf_to_jsonld["self"]: node["data"]["links"]["self"],
            osf_to_jsonld["storages_url"]: node["data"]["relationships"]["files"][
                "links"
            ]["related"]["href"],
        }
    )

    return data


def _build_node(type_):
    node = json.loads(node_json)
    node["data"]["type"] = type_
    return node


project_node = _build_node("nodes")
registration_node = _build_node("registrations")
fake_node = _build_node("fakes")
jsonld_attributes = _make_jsonld()

# Use this to fake a response when asking for a project's files/storages
# e.g. project.storages or project.storage()
def storage_node(project_id, storages=["osfstorage"]):
    storage = """
    {
        "relationships": {
            "files": {
                "links": {
                    "related": {
                        "href": "https://api.osf.io/v2/nodes/%(project_id)s/files/%(name)s/",
                        "meta": {}
                    }
                }
            }
        },
        "links": {
            "storage_addons": "https://api.osf.io/v2/addons/?filter%%5Bcategories%%5D=storage",
            "upload": "https://files.osf.io/v1/resources/%(project_id)s/providers/%(name)s/",
            "new_folder": "https://files.osf.io/v1/resources/%(project_id)s/providers/%(name)s/?kind=folder"
        },
        "attributes": {
            "node": "%(project_id)s",
            "path": "/",
            "kind": "folder",
            "name": "%(name)s",
            "provider": "%(name)s"
        },
        "type": "files",
        "id": "%(project_id)s:%(name)s"
    }"""
    used_storages = []
    for store in storages:
        used_storages.append(
            json.loads(storage % {"project_id": project_id, "name": store})
        )

    files = """{
    "data": %(storages)s,
    "links": {
        "first": null,
        "last": null,
        "prev": null,
        "next": null,
        "meta": {
            "total": %(n_storages)s,
            "per_page": 10
        }
    }
    }"""
    return json.loads(
        files
        % {"storages": json.dumps(used_storages), "n_storages": len(used_storages)}
    )


def _folder(osf_id, name, storage="osfstorage"):
    template = """{
        "relationships": {
            "files": {
                "links": {
                    "related": {
                        "href": "https://api.osf.io/v2/nodes/9zpcy/files/%(storage)s/%(osf_id)s/",
                        "meta": {}
                    }
                }
            },
            "node": {
                "links": {
                    "related": {
                        "href": "https://api.osf.io/v2/nodes/9zpcy/",
                        "meta": {}
                    }
                }
            }
        },
        "links": {
            "info": "https://api.osf.io/v2/files/%(osf_id)s/",
            "new_folder": "https://files.osf.io/v1/resources/9zpcy/providers/%(storage)s/%(osf_id)s/?kind=folder",
            "self": "https://api.osf.io/v2/files/%(osf_id)s/",
            "move": "https://files.osf.io/v1/resources/9zpcy/providers/%(storage)s/%(osf_id)s/",
            "upload": "https://files.osf.io/v1/resources/9zpcy/providers/%(storage)s/%(osf_id)s/",
            "delete": "https://files.osf.io/v1/resources/9zpcy/providers/%(storage)s/%(osf_id)s/"
        },
        "attributes": {
            "extra": {
                "hashes": {
                    "sha256": null,
                    "md5": null
                }
            },
            "kind": "folder",
            "name": "%(name)s",
            "last_touched": null,
            "materialized_path": "/%(name)s/",
            "date_modified": null,
            "current_version": 1,
            "delete_allowed": true,
            "date_created": null,
            "provider": "%(storage)s",
            "path": "/%(osf_id)s/",
            "current_user_can_comment": true,
            "guid": null,
            "checkout": null,
            "tags": [],
            "size": null
        },
        "type": "files",
        "id": "%(osf_id)s"
    }"""
    return json.loads(template % dict(osf_id=osf_id, name=name, storage=storage))


def files_node(project_id, storage, file_names=["hello.txt"], folder_names=None):
    a_file = """{
    "relationships": {
        "node": {
            "links": {
                "related": {
                    "href": "https://api.osf.io/v2/nodes/%(project_id)s/",
                    "meta": {}
                }
            }
        },
        "versions": {
            "links": {
                "related": {
                    "href": "https://api.osf.io/v2/files/58becc229ad5a101f98293a3/versions/",
                    "meta": {}
                }
            }
        }
    },
    "links": {
        "info": "https://api.osf.io/v2/files/58becc229ad5a101f98293a3/",
        "self": "https://api.osf.io/v2/files/58becc229ad5a101f98293a3/",
        "move": "https://files.osf.io/v1/resources/%(project_id)s/providers/%(storage)s/%(fname)s",
        "upload": "https://files.osf.io/v1/resources/%(project_id)s/providers/%(storage)s/%(fname)s",
        "download": "https://files.osf.io/v1/resources/%(project_id)s/providers/%(storage)s/%(fname)s",
        "delete": "https://files.osf.io/v1/resources/%(project_id)s/providers/%(storage)s/%(fname)s",
        "html": "https://osf.io/%(project_id)s/files/%(storage)s/58becc229ad5a101f98293a3"
    },
    "attributes": {
        "extra": {
            "hashes": {
                "sha256": null,
                "md5": null
            }
        },
        "kind": "file",
        "name": "%(fname)s",
        "last_touched": "2017-03-20T16:24:57.417044",
        "materialized_path": "/%(fname)s",
        "date_modified": null,
        "current_version": 1,
        "date_created": null,
        "provider": "%(storage)s",
        "path": "/%(fname)s",
        "current_user_can_comment": true,
        "guid": null,
        "checkout": null,
        "tags": [],
        "size": null
    },
    "type": "files",
    "id": "58becc229ad5a101f98293a3"
}"""
    files = []
    for fname in file_names:
        files.append(
            json.loads(
                a_file % dict(storage=storage, fname=fname, project_id=project_id)
            )
        )

    if folder_names is not None:
        for folder in folder_names:
            files.append(_folder(folder + "123", folder, storage))

    wrapper = """{
    "data": %(files)s,
    "links": {
        "first": null,
        "last": null,
        "prev": null,
        "next": null,
        "meta": {
            "total": %(n_files)s,
            "per_page": %(n_files)s
        }
    }
    }"""
    return json.loads(wrapper % {"files": json.dumps(files), "n_files": len(files)})

