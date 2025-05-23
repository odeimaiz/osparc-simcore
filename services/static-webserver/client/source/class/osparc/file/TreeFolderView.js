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

/**
 * Reload button
 * -------------------------------- =/- -
 * | root        |  content1  content2  |
 * |   folder1   |  content3  content4  |
 * |     folder2 |  content5  content6  |
 * --------------------------------------
 *              selected_file   Down  Del
 */

qx.Class.define("osparc.file.TreeFolderView", {
  extend: qx.ui.core.Widget,

  construct: function() {
    this.base(arguments);

    this._setLayout(new qx.ui.layout.VBox(10));

    this.__buildLayout();
  },

  members: {
    _createChildControlImpl: function(id) {
      let control;
      switch (id) {
        case "header-layout":
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox()).set({
            marginLeft: 8
          });
          this._addAt(control, 0);
          break;
        case "reload-button":
          control = new qx.ui.form.Button().set({
            label: this.tr("Reload"),
            font: "text-14",
            icon: "@FontAwesome5Solid/sync-alt/14",
            allowGrowX: false
          });
          this.getChildControl("header-layout").add(control);
          break;
        case "total-size-label":
          control = new qx.ui.basic.Atom().set({
            label: this.tr("Calculating Size"),
            font: "text-14",
            icon: "@FontAwesome5Solid/spinner/14",
            allowGrowX: false
          });
          osparc.utils.Utils.setIdToWidget(control.getChildControl("label"), "totalSizeLabel");
          this.getChildControl("header-layout").add(control);
          break;
        case "tree-folder-layout":
          control = new qx.ui.splitpane.Pane("horizontal");
          control.getChildControl("splitter").set({
            width: 2,
            backgroundColor: "scrollbar-passive"
          });
          this._add(control, {
            flex: 1
          });
          break;
        case "folder-tree": {
          const treeFolderLayout = this.getChildControl("tree-folder-layout");
          control = new osparc.file.FilesTree().set({
            showLeafs: false,
            minWidth: 150,
            width: 250
          });
          treeFolderLayout.add(control, 0);
          break;
        }
        case "folder-viewer": {
          const treeFolderLayout = this.getChildControl("tree-folder-layout");
          control = new osparc.file.FolderViewer();
          treeFolderLayout.add(control, 1);
          break;
        }
      }
      return control || this.base(arguments, id);
    },

    __openPath: function(selectedModel) {
      const folderTree = this.getChildControl("folder-tree");
      if (selectedModel.getPath() && !selectedModel.getLoaded()) {
        selectedModel.setLoaded(true);
        folderTree.requestPathItems(selectedModel.getLocation(), selectedModel.getPath())
          .then(() => {
            folderTree.openNodeAndParents(selectedModel);
            folderTree.setSelection(new qx.data.Array([selectedModel]));
          })
          .catch(err => {
            console.error(err);
            selectedModel.setLoaded(false);
          });
      } else {
        folderTree.openNodeAndParents(selectedModel);
        folderTree.setSelection(new qx.data.Array([selectedModel]));
      }

      const folderViewer = this.getChildControl("folder-viewer");
      if (osparc.file.FilesTree.isDir(selectedModel)) {
        folderViewer.setFolder(selectedModel);
      }
    },

    __buildLayout: function() {
      const folderTree = this.getChildControl("folder-tree");
      const folderViewer = this.getChildControl("folder-viewer");

      folderTree.addListener("selectionChanged", () => {
        const selectedModel = folderTree.getSelectedItem();
        if (selectedModel) {
          this.__openPath(selectedModel);
        }
      }, this);

      folderViewer.addListener("openItemSelected", e => {
        const selectedModel = e.getData();
        if (selectedModel) {
          this.__openPath(selectedModel);
        }
      }, this);

      folderViewer.addListener("folderUp", e => {
        const currentFolder = e.getData();
        const parent = folderTree.getParent(currentFolder);
        if (parent) {
          this.__openPath(parent);
        }
      }, this);
    },

    pathsDeleted: function(paths) {
      this.getChildControl("folder-viewer").resetSelection();

      const folderTree = this.getChildControl("folder-tree");
      const selectedFolder = folderTree.getSelectedItem();
      const children = selectedFolder.getChildren();
      paths.forEach(path => {
        const found = children.toArray().find(child => child.getPath() === path);
        if (found) {
          children.remove(found);
        }
      });
    },

    requestSize: function(pathId) {
      const totalSize = this.getChildControl("total-size-label");
      totalSize.getChildControl("icon").getContentElement().addClass("rotate");

      const pollTasks = osparc.store.PollTasks.getInstance();
      const fetchPromise = osparc.data.Resources.fetch("storagePaths", "requestSize", { url: { pathId } })
      pollTasks.createPollingTask(fetchPromise)
        .then(task => {
          task.addListener("resultReceived", e => {
            const data = e.getData();
            const size = (data && "result" in data) ? osparc.utils.Utils.bytesToSize(data["result"]) : "-";
            totalSize.set({
              icon: null,
              label: this.tr("Total size: ") + size,
            });
          });
          task.addListener("pollingError", () => totalSize.hide());
        })
        .catch(err => {
          console.error(err);
          totalSize.hide();
        });
    }
  }
});
