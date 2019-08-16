/*
 * oSPARC - The SIMCORE frontend - https://osparc.io
 * Copyright: 2019 IT'IS Foundation - https://itis.swiss
 * License: MIT - https://opensource.org/licenses/MIT
 * Authors: Ignacio Pascual (ignapas)
 *          Odei Maiz (odeimaiz)
 */

qx.Class.define("qxapp.component.metadata.StudyDetails", {
  extend: qx.ui.core.Widget,

  construct: function(study) {
    this.base(arguments);
    this._setLayout(new qx.ui.layout.VBox(10));

    this.__model = qx.data.marshal.Json.createModel(study);

    const hBox = new qx.ui.container.Composite(new qx.ui.layout.HBox(8));
    hBox.add(this.__createThumbnail(), {
      flex: 1
    });
    hBox.add(this.__createExtraInfo());
    this._add(hBox);
    this._add(this.__createTitle());
    this._add(this.__createDescription());
  },

  members: {
    __model: null,

    __createThumbnail: function() {
      const image = new qx.ui.basic.Image().set({
        scale: true,
        allowStretchX: true,
        allowStretchY: true,
        maxHeight: 200,
        alignX: "center"
      });

      this.__model.bind("thumbnail", image, "source");
      this.__model.bind("thumbnail", image, "visibility", {
        converter: thumbnail => {
          if (thumbnail) {
            return "visible";
          }
          return "excluded";
        }
      });

      return image;
    },

    __createExtraInfo: function() {
      const grid = new qx.ui.layout.Grid(5, 3);
      grid.setColumnAlign(0, "right", "middle");
      grid.setColumnAlign(1, "left", "middle");
      grid.setColumnFlex(0, 1);
      grid.setColumnFlex(1, 1);
      const moreInfo = new qx.ui.container.Composite(grid).set({
        maxWidth: 220,
        alignY: "middle"
      });

      const creationDate = new qx.ui.basic.Label();
      const lastChangeDate = new qx.ui.basic.Label();
      const owner = new qx.ui.basic.Label();

      const dateOptions = {
        converter: date => new Date(date).toLocaleString()
      };
      this.__model.bind("creationDate", creationDate, "value", dateOptions);
      this.__model.bind("lastChangeDate", lastChangeDate, "value", dateOptions);
      this.__model.bind("prjOwner", owner, "value");

      moreInfo.add(new qx.ui.basic.Label(this.tr("Owner")).set({
        font: "title-12"
      }), {
        row: 0,
        column: 0
      });
      moreInfo.add(owner, {
        row: 0,
        column: 1
      });
      moreInfo.add(new qx.ui.basic.Label(this.tr("Creation date")).set({
        font: "title-12"
      }), {
        row: 1,
        column: 0
      });
      moreInfo.add(creationDate, {
        row: 1,
        column: 1
      });
      moreInfo.add(new qx.ui.basic.Label(this.tr("Last modified")).set({
        font: "title-12"
      }), {
        row: 2,
        column: 0
      });
      moreInfo.add(lastChangeDate, {
        row: 2,
        column: 1
      });

      return moreInfo;
    },

    __createButtons: function() {
      const canCreateTemplate = qxapp.data.Permissions.getInstance().canDo("studies.template.create");
      const isCurrentUserOwner = this.__model.getPrjOwner() === qxapp.data.Permissions.getInstance().getLogin();
      const canUpdateTemplate = qxapp.data.Permissions.getInstance().canDo("studies.template.update");

      const buttonsLayout = new qx.ui.container.Composite(new qx.ui.layout.HBox(8).set({
        alignY: "middle"
      })).set({
        marginTop: 10
      });

      const openButton = new qx.ui.form.Button("Open").set({
        appearance: "md-button"
      });
      openButton.addListener("execute", () => this.fireEvent("openedStudy"), this);
      buttonsLayout.add(openButton);

      const modeButton = new qx.ui.form.Button("Edit", "@FontAwesome5Solid/edit/16").set({
        appearance: "md-button",
        visibility: isCurrentUserOwner && (!this.__isTemplate || canUpdateTemplate) ? "visible" : "excluded"
      });
      modeButton.addListener("execute", () => this.setMode("edit"), this);
      buttonsLayout.add(modeButton);

      buttonsLayout.add(new qx.ui.core.Spacer(), {
        flex: 1
      });

      if (isCurrentUserOwner && (!this.__isTemplate && canCreateTemplate)) {
        const saveAsTemplateButton = new qx.ui.form.Button(this.tr("Save as template")).set({
          appearance: "md-button"
        });
        saveAsTemplateButton.addListener("execute", e => {
          const btn = e.getTarget();
          btn.setIcon("@FontAwesome5Solid/circle-notch/12");
          btn.getChildControl("icon").getContentElement()
            .addClass("rotate");
          this.__saveAsTemplate(btn);
        }, this);
        buttonsLayout.add(saveAsTemplateButton);
      }

      return buttonsLayout;
    },

    __createTitle: function() {
      const title = new qx.ui.basic.Label().set({
        font: "nav-bar-label",
        allowStretchX: true,
        rich: true
      });

      this.__model.bind("name", title, "value");

      return title;
    },

    __createDescription: function() {
      const description = new qxapp.ui.markdown.Markdown();

      this.__model.bind("description", description, "markdown");

      return description;
    },

    __createEditView: function() {
      const isCurrentUserOwner = this.__model.getPrjOwner() === qxapp.data.Permissions.getInstance().getLogin();
      const canUpdateTemplate = qxapp.data.Permissions.getInstance().canDo("studies.template.update");
      const fieldIsEnabled = isCurrentUserOwner && (!this.__isTemplate || canUpdateTemplate);

      const editView = new qx.ui.container.Composite(new qx.ui.layout.VBox(8));
      const buttons = new qx.ui.container.Composite(new qx.ui.layout.HBox(8).set({
        alignX: "right"
      }));

      this.__fields = {
        name: new qx.ui.form.TextField(this.__model.getName()).set({
          font: "title-18",
          height: 35,
          enabled: fieldIsEnabled
        }),
        description: new qx.ui.form.TextArea(this.__model.getDescription()).set({
          autoSize: true,
          minHeight: 100,
          maxHeight: 500,
          enabled: fieldIsEnabled
        }),
        thumbnail: new qx.ui.form.TextField(this.__model.getThumbnail()).set({
          enabled: fieldIsEnabled
        })
      };

      const modeButton = new qx.ui.form.Button("Save", "@FontAwesome5Solid/save/16").set({
        appearance: "md-button"
      });
      modeButton.addListener("execute", e => {
        const btn = e.getTarget();
        btn.setIcon("@FontAwesome5Solid/circle-notch/16");
        btn.getChildControl("icon").getContentElement()
          .addClass("rotate");
        this.__saveStudy(btn);
      }, this);
      const cancelButton = new qx.ui.form.Button(this.tr("Cancel")).set({
        appearance: "md-button",
        enabled: isCurrentUserOwner && (!this.__isTemplate || canUpdateTemplate)
      });
      cancelButton.addListener("execute", () => this.setMode("display"), this);

      const {
        name,
        description,
        thumbnail
      } = this.__fields;
      editView.add(new qx.ui.basic.Label(this.tr("Title")).set({
        font: "text-14",
        marginTop: 20
      }));
      editView.add(name);
      editView.add(new qx.ui.basic.Label(this.tr("Description")).set({
        font: "text-14"
      }));
      editView.add(description);
      editView.add(new qx.ui.basic.Label(this.tr("Thumbnail")).set({
        font: "text-14"
      }));
      editView.add(thumbnail);
      editView.add(buttons);

      buttons.add(modeButton);
      buttons.add(cancelButton);

      return editView;
    },

    __saveStudy: function(btn) {
      const apiCall = qxapp.io.rest.ResourceFactory.getInstance().createStudyResources().project;
      apiCall.addListenerOnce("putSuccess", e => {
        btn.resetIcon();
        btn.getChildControl("icon").getContentElement()
          .removeClass("rotate");
        this.fireDataEvent(this.__isTemplate ? "updatedTemplate" : "updatedStudy", e);
        const data = e.getData().data;
        this.__model.set(data);
        this.setMode("display");
      }, this);
      apiCall.put({
        "project_id": this.__model.getUuid()
      }, this.__serializeForm());
    },

    __saveAsTemplate: function(btn) {
      const apiCall = qxapp.io.rest.ResourceFactory.getInstance().createStudyResources().projects;
      apiCall.addListenerOnce("postSaveAsTemplateSuccess", e => {
        btn.resetIcon();
        btn.getChildControl("icon").getContentElement()
          .removeClass("rotate");
        this.fireDataEvent("updatedTemplate", e);
        const data = e.getData().data;
        this.__model.set(data);
        this.setMode("display");
      }, this);
      apiCall.addListenerOnce("postSaveAsTemplateError", e => {
        btn.resetIcon();
        console.error(e);
      }, this);
      apiCall.postSaveAsTemplate({
        "study_id": this.__model.getUuid()
      }, this.__serializeForm());
    },

    __serializeForm: function() {
      const data = {
        ...qx.util.Serializer.toNativeObject(this.__model),
        workbench: this.__workbench
      };
      for (let key in this.__fields) {
        data[key] = this.__fields[key].getValue();
      }
      return data;
    },

    _applyMode: function(mode) {
      switch (mode) {
        case "display":
          this.__stack.setSelection([this.__displayView]);
          break;
        case "edit":
          this.__stack.setSelection([this.__editView]);
          break;
      }
    }
  }
});
