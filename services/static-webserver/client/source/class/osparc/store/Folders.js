/* ************************************************************************

   osparc - the simcore frontend

   https://osparc.io

   Copyright:
     2024 IT'IS Foundation, https://itis.swiss

   License:
     MIT: https://opensource.org/licenses/MIT

   Authors:
     * Odei Maiz (odeimaiz)

************************************************************************ */

qx.Class.define("osparc.store.Folders", {
  extend: qx.core.Object,
  type: "singleton",

  construct: function() {
    this.base(arguments);

    this.foldersCached = [];
  },

  events: {
    "folderAdded": "qx.event.type.Data",
    "folderRemoved": "qx.event.type.Data",
    "folderMoved": "qx.event.type.Data",
  },

  members: {
    foldersCached: null,

    fetchFolders: function(
      folderId = null,
      workspaceId = null,
      orderBy = {
        field: "modified_at",
        direction: "desc"
      }
    ) {
      if (osparc.auth.Data.getInstance().isGuest()) {
        return new Promise(resolve => {
          resolve([]);
        });
      }

      const curatedOrderBy = osparc.utils.Utils.deepCloneObject(orderBy);
      if (curatedOrderBy.field !== "name") {
        // only "modified_at" and "name" supported
        curatedOrderBy.field = "modified_at";
      }

      const params = {
        url: {
          workspaceId,
          folderId,
          orderBy: JSON.stringify(curatedOrderBy),
        }
      };
      return osparc.data.Resources.getInstance().getAllPages("folders", params)
        .then(foldersData => {
          const folders = [];
          foldersData.forEach(folderData => {
            const folder = this.__addToCache(folderData);
            folders.push(folder);
          });
          return folders;
        });
    },

    postFolder: function(name, parentFolderId = null, workspaceId = null) {
      const newFolderData = {
        name,
        parentFolderId,
        workspaceId,
      };
      const params = {
        data: newFolderData
      };
      return osparc.data.Resources.getInstance().fetch("folders", "post", params)
        .then(folderData => {
          const folder = this.__addToCache(folderData);
          this.fireDataEvent("folderAdded", folder);
          return folder;
        });
    },

    deleteFolder: function(folderId, workspaceId) {
      const params = {
        "url": {
          folderId
        }
      };
      return osparc.data.Resources.getInstance().fetch("folders", "delete", params)
        .then(() => {
          const folder = this.getFolder(folderId);
          if (folder) {
            this.__deleteFromCache(folderId, workspaceId);
            this.fireDataEvent("folderRemoved", folder);
          }
        })
        .catch(console.error);
    },

    putFolder: function(folderId, updateData) {
      const folder = this.getFolder(folderId);
      const oldParentFolderId = folder.getParentFolderId();
      const params = {
        "url": {
          folderId
        },
        data: updateData
      };
      return osparc.data.Resources.getInstance().fetch("folders", "update", params)
        .then(folderData => {
          this.__addToCache(folderData);
          if (updateData.parentFolderId !== oldParentFolderId) {
            this.fireDataEvent("folderMoved", {
              folder,
              oldParentFolderId,
            });
          }
        })
        .catch(console.error);
    },

    getFolder: function(folderId = null) {
      return this.foldersCached.find(f => f.getFolderId() === folderId);
    },

    __addToCache: function(folderData) {
      let folder = this.foldersCached.find(f => f.getFolderId() === folderData["folderId"] && f.getWorkspaceId() === folderData["workspaceId"]);
      if (folder) {
        // put
        Object.keys(folderData).forEach(key => {
          if (key === "createdAt") {
            folder.set("createdAt", new Date(folderData["createdAt"]));
          } else if (key === "modifiedAt") {
            folder.set("lastModified", new Date(folderData["modifiedAt"]));
          } else {
            folder.set(key, folderData[key]);
          }
        });
      } else {
        // get and post
        folder = new osparc.data.model.Folder(folderData);
        this.foldersCached.unshift(folder);
      }
      return folder;
    },

    __deleteFromCache: function(folderId, workspaceId) {
      const idx = this.foldersCached.findIndex(f => f.getFolderId() === folderId && f.getWorkspaceId() === workspaceId);
      if (idx > -1) {
        this.foldersCached.splice(idx, 1);
        return true;
      }
      return false;
    }
  }
});
