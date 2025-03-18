/* ************************************************************************

   osparc - the simcore frontend

   https://osparc.io

   Copyright:
     2018 IT'IS Foundation, https://itis.swiss

   License:
     MIT: https://opensource.org/licenses/MIT

   Authors:
     * Odei Maiz (odeimaiz)

************************************************************************ */

/**
 * Singleton class that is used as entrypoint to the webserver.
 *
 * All data transfer communication goes through the osparc.store.Store.
 */

qx.Class.define("osparc.store.Data", {
  extend: qx.core.Object,
  type: "singleton",

  construct: function() {
    this.resetCache();

    this.getLocations();
  },

  events: {
    "fileCopied": "qx.event.type.Data",
  },

  members: {
    __locationsCached: null,
    __datasetsByLocationCached: null,

    resetCache: function() {
      this.__locationsCached = [];
      this.__datasetsByLocationCached = {};
    },

    getLocationsCached: function() {
      const cache = this.__locationsCached;
      if (cache && cache.length) {
        return cache;
      }
      return null;
    },

    getLocations: function() {
      return new Promise((resolve, reject) => {
        const cachedData = this.getLocationsCached();
        if (cachedData) {
          resolve(cachedData);
        } else {
          osparc.data.Resources.fetch("storageLocations", "getLocations")
            .then(locations => {
              // Add them to cache
              this.__locationsCached = locations;
              resolve(locations);
            })
            .catch(err => {
              console.error(err);
              reject([]);
            });
        }
      });
    },

    getDatasetsByLocationCached: function(locationId) {
      const cache = this.__datasetsByLocationCached;
      if (locationId in cache && cache[locationId] && cache[locationId].length) {
        const data = {
          location: locationId,
          items: cache[locationId]
        };
        return data;
      }
      return null;
    },

    getDatasetsByLocation: function(locationId) {
      const data = {
        location: locationId,
        items: []
      };
      return new Promise((resolve, reject) => {
        if (locationId === 1 && !osparc.data.Permissions.getInstance().canDo("storage.datcore.read")) {
          reject(data);
        }

        const cachedData = this.getDatasetsByLocationCached(locationId);
        if (cachedData) {
          resolve(cachedData);
        } else {
          const params = {
            url: {
              locationId
            }
          };
          osparc.data.Resources.fetch("storagePaths", "getDatasets", params)
            .then(pagResp => {
              if (pagResp["items"] && pagResp["items"].length>0) {
                data.items = pagResp["items"];
              }
              // Add it to cache
              this.__datasetsByLocationCached[locationId] = data.items;
              resolve(data);
            })
            .catch(err => {
              console.error(err);
              reject(data);
            });
        }
      });
    },

    getItemsByLocationAndPath: async function(locationId, path) {
      // Get list of file meta data
      if (locationId === 1 && !osparc.data.Permissions.getInstance().canDo("storage.datcore.read")) {
        return [];
      }

      try {
        const allItems = await this.__getAllItems(locationId, path);
        return allItems;
      } catch (err) {
        console.error(err);
        return [];
      }
    },

    __getAllItems: async function(locationId, path, cursor, allItems = []) {
      if (allItems.length >= 10000) {
        const msg = this.tr("Oops... more than 10.000 files to be listed here. Maybe it's time to make a folder :).");
        osparc.FlashMessenger.logAs(msg, "WARNING");
        return allItems;
      }
      const params = {
        url: {
          locationId,
          path,
        }
      };
      if (cursor) {
        params["url"]["cursor"] = cursor;
      }
      const pagResp = await osparc.data.Resources.fetch("storagePaths", cursor ? "getPathsPage" : "getPaths", params);
      if (pagResp["items"]) {
        allItems.push(...pagResp["items"]);
      }
      let nextCursor = null;
      if (pagResp["next_page"]) {
        nextCursor = pagResp["next_page"];
      }
      if (nextCursor) {
        return this.__getAllItems(locationId, path, nextCursor, allItems);
      }
      return allItems;
    },

    getPresignedLink: function(download = true, locationId, fileUuid, fileSize) {
      return new Promise((resolve, reject) => {
        if (download && !osparc.data.Permissions.getInstance().canDo("study.node.data.pull", true)) {
          reject();
        }
        if (!download && !osparc.data.Permissions.getInstance().canDo("study.node.data.push", true)) {
          reject();
        }

        // GET: Returns download link for requested file
        // PUT: Returns upload object link(s)
        const params = {
          url: {
            locationId,
            fileUuid: encodeURIComponent(fileUuid)
          }
        };
        if (!download && fileSize) {
          params.url["fileSize"] = fileSize;
        }
        osparc.data.Resources.fetch("storageLink", download ? "getOne" : "put", params)
          .then(data => {
            const presignedLinkData = {
              resp: data,
              locationId,
              fileUuid,
              fileSize
            };
            resolve(presignedLinkData);
          })
          .catch(err => {
            console.error(err);
            reject(err);
          });
      });
    },

    copyFile: function(fromLoc, fileUuid, toLoc, pathId) {
      if (!osparc.data.Permissions.getInstance().canDo("study.node.data.push", true)) {
        return false;
      }

      // "/v0/locations/1/files/{}?user_id={}&extra_location={}&extra_source={}".format(quote(datcore_uuid, safe=''),
      let fileName = fileUuid.split("/");
      fileName = fileName[fileName.length-1];

      const params = {
        url: {
          toLoc,
          fileName: encodeURIComponent(pathId + "/" + fileName),
          fromLoc,
          fileUuid: encodeURIComponent(fileUuid)
        }
      };
      osparc.data.Resources.fetch("storageFiles", "copy", params)
        .then(files => {
          const data = {
            data: files,
            locationId: toLoc,
            fileUuid: pathId + "/" + fileName
          };
          this.fireDataEvent("fileCopied", data);
        })
        .catch(err => {
          osparc.FlashMessenger.logError(err, this.tr("Unsuccessful file copy"));
          this.fireDataEvent("fileCopied", null);
        });

      return true;
    },

    // if folder path is provided as fileUuid, it can also be deleted
    deleteFile: function(locationId, fileUuid) {
      if (!osparc.data.Permissions.getInstance().canDo("study.node.data.delete", true)) {
        return null;
      }

      // Deletes File
      const params = {
        url: {
          locationId,
          fileUuid: encodeURIComponent(fileUuid)
        }
      };
      return osparc.data.Resources.fetch("storageFiles", "delete", params)
        .then(files => {
          const data = {
            data: files,
            locationId: locationId,
            fileUuid: fileUuid
          };
          return data;
        })
        .catch(err => osparc.FlashMessenger.logError(err, this.tr("Unsuccessful file deletion")));
    }
  }
});
