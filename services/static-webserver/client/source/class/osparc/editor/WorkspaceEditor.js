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

qx.Class.define("osparc.editor.WorkspaceEditor", {
  extend: qx.ui.core.Widget,

  construct: function(workspace) {
    this.base(arguments);

    this._setLayout(new qx.ui.layout.VBox(8));

    if (!workspace) {
      this.getChildControl("intro-text");
    }

    const manager = this.__validator = new qx.ui.form.validation.Manager();
    const title = this.getChildControl("title");
    title.setRequired(true);
    manager.add(title);
    this.getChildControl("description");
    this.getChildControl("thumbnail");
    this.getChildControl("cancel");
    const saveButton = this.getChildControl("save");
    if (workspace) {
      // editing
      this.setWorkspace(workspace);
    } else {
      // creating
      this.__creatingWorkspace = true;
      saveButton.setLabel(this.tr("Create"));
      this.__createWorkspace()
        .then(newWorkspace => {
          this.setWorkspace(newWorkspace);
          this.fireDataEvent("workspaceCreated", newWorkspace);
          this.getChildControl("sharing");
        });
    }

    this.addListener("appear", this.__onAppear, this);
  },

  properties: {
    workspace: {
      check: "osparc.data.model.Workspace",
      init: null,
      nullable: false,
      apply: "__applyWorkspace"
    },

    label: {
      check: "String",
      init: "",
      nullable: false,
      event: "changeLabel"
    },

    description: {
      check: "String",
      init: "",
      nullable: false,
      event: "changeDescription"
    },

    thumbnail: {
      check: "String",
      init: "",
      nullable: false,
      event: "changeThumbnail"
    },
  },

  events: {
    "workspaceCreated": "qx.event.type.Data",
    "workspaceUpdated": "qx.event.type.Event",
    "updateAccessRights": "qx.event.type.Event",
    "cancel": "qx.event.type.Event"
  },

  statics: {
    POS: {
      INTRO: 0,
      TITLE: 1,
      DESCRIPTION: 2,
      THUMBNAIL: 3,
      SHARING: 4,
      BUTTONS: 5,
    }
  },

  members: {
    __creatingWorkspace: null,

    _createChildControlImpl: function(id) {
      let control;
      switch (id) {
        case "intro-text": {
          const studies = osparc.product.Utils.getStudyAlias({ plural: true });
          const text = this.tr(`A Shared Workspace is the context where all the ${studies} and folders are shared among its members.`);
          control = new qx.ui.basic.Label(text).set({
            font: "text-14",
            rich: true,
            wrap: true
          });
          this._addAt(control, this.self().POS.INTRO);
          break;
        }
        case "title": {
          control = new qx.ui.form.TextField().set({
            font: "text-14",
            backgroundColor: "background-main",
            placeholder: this.tr("Title"),
            minHeight: 27
          });
          this.bind("label", control, "value");
          control.bind("value", this, "label");
          this._addAt(control, this.self().POS.TITLE);
          break;
        }
        case "description": {
          control = new qx.ui.form.TextField().set({
            font: "text-14",
            placeholder: this.tr("Description"),
          });
          this.bind("description", control, "value");
          control.bind("value", this, "description");
          this._addAt(control, this.self().POS.DESCRIPTION);
          break;
        }
        case "thumbnail": {
          control = new qx.ui.form.TextField().set({
            font: "text-14",
            placeholder: this.tr("Thumbnail"),
          });
          this.bind("thumbnail", control, "value");
          control.bind("value", this, "thumbnail");
          this._addAt(control, this.self().POS.THUMBNAIL);
          break;
        }
        case "sharing": {
          control = new osparc.share.CollaboratorsWorkspace(this.getWorkspace());
          control.addListener("updateAccessRights", () => this.fireDataEvent("updateAccessRights", this.getWorkspace().getWorkspaceId()), this);
          this._addAt(control, this.self().POS.SHARING);
          break;
        }
        case "buttons-layout": {
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox(8).set({
            alignX: "right"
          }));
          this._addAt(control, this.self().POS.BUTTONS);
          break;
        }
        case "save": {
          const buttons = this.getChildControl("buttons-layout");
          control = new osparc.ui.form.FetchButton(this.tr("Save")).set({
            appearance: "form-button"
          });
          control.addListener("execute", () => this.__saveWorkspace(control), this);
          buttons.addAt(control, 1);
          break;
        }
        case "cancel": {
          const buttons = this.getChildControl("buttons-layout");
          control = new qx.ui.form.Button(this.tr("Cancel")).set({
            appearance: "form-button-text"
          });
          control.addListener("execute", () => this.cancel(), this);
          buttons.addAt(control, 0);
          break;
        }
      }

      return control || this.base(arguments, id);
    },

    __applyWorkspace: function(workspace) {
      this.set({
        label: workspace.getName(),
        description: workspace.getDescription(),
        thumbnail: workspace.getThumbnail(),
      });
    },

    __createWorkspace: function() {
      const newWorkspaceData = {
        name: this.getLabel() || "New Workspace",
        description: this.getDescription(),
        thumbnail: this.getThumbnail(),
      };
      return osparc.store.Workspaces.getInstance().postWorkspace(newWorkspaceData)
    },

    __saveWorkspace: function(editButton) {
      if (this.__validator.validate()) {
        editButton.setFetching(true);
        const updateData = {
          name: this.getLabel(),
          description: this.getDescription(),
          thumbnail: this.getThumbnail(),
        };
        osparc.store.Workspaces.getInstance().putWorkspace(this.getWorkspace().getWorkspaceId(), updateData)
          .then(() => this.fireEvent("workspaceUpdated"))
          .catch(err => {
            console.error(err);
            osparc.FlashMessenger.logAs(err.message, "ERROR");
          })
          .finally(() => editButton.setFetching(false));
      }
    },

    cancel: function() {
      if (this.__creatingWorkspace) {
        osparc.store.Workspaces.getInstance().deleteWorkspace(this.getWorkspace().getWorkspaceId());
      }
      this.fireEvent("cancel");
    },

    __onAppear: function() {
      const title = this.getChildControl("title");
      title.focus();
      title.activate();
    }
  }
});
