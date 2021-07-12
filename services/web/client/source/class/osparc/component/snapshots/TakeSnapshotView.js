/* ************************************************************************

   osparc - the simcore frontend

   https://osparc.io

   Copyright:
     2021 IT'IS Foundation, https://itis.swiss

   License:
     MIT: https://opensource.org/licenses/MIT

   Authors:
     * Odei Maiz (odeimaiz)

************************************************************************ */

qx.Class.define("osparc.component.snapshots.TakeSnapshotView", {
  extend: qx.ui.core.Widget,

  construct: function(study) {
    this.base(arguments);

    this._setLayout(new qx.ui.layout.VBox(10));

    this.set({
      study
    });

    this.__buildForm();
  },

  events: {
    "takeSnapshot": "qx.event.type.Event",
    "cancel": "qx.event.type.Event"
  },

  properties: {
    study: {
      check: "osparc.data.model.Study",
      init: null,
      nullable: false
    }
  },

  members: {
    __form: null,

    _createChildControlImpl: function(id) {
      let control;
      switch (id) {
        case "label":
          control = new qx.ui.form.TextField();
          break;
        case "save-data":
          control = new qx.ui.form.CheckBox().set({
            value: false,
            enabled: false
          });
          break;
        case "cancel-button": {
          control = new qx.ui.form.Button(this.tr("Cancel")).set({
            allowGrowX: false
          });
          control.addListener("execute", () => this.fireEvent("cancel"));
          break;
        }
        case "ok-button": {
          control = new qx.ui.form.Button(this.tr("OK")).set({
            allowGrowX: false
          });
          control.addListener("execute", () => this.fireEvent("takeSnapshot"));
          break;
        }
      }
      return control || this.base(arguments, id);
    },

    __buildForm: function() {
      const form = this.__form = new qx.ui.form.Form();
      this._add(new qx.ui.form.renderer.Single(form));

      const study = this.getStudy();

      const label = this.getChildControl("label");
      form.add(label, "Label", null, "label");
      label.setValue(study.getName());

      const saveWData = this.getChildControl("save-data");
      form.add(saveWData, "Save with Data", null, "save-data");

      // buttons
      const cancelButton = this.getChildControl("cancel-button");
      form.addButton(cancelButton);
      const okButton = this.getChildControl("ok-button");
      form.addButton(okButton);
    },

    getLabel: function() {
      return this.__form.getItem("label").getValue();
    },

    getSaveData: function() {
      return this.__form.getItem("save-data").getValue();
    }
  }
});
