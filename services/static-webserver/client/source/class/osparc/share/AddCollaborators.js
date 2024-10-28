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
 *   Widget that offers the "Share with..." button to add collaborators to a resource.
 *   It also provides the "Check Organization..." direct access.
 *   As output, once the user select n gid in the NewCollaboratorsManager pop up window,
 * an event is fired with the list of collaborators.
 */

qx.Class.define("osparc.share.AddCollaborators", {
  extend: qx.ui.core.Widget,

  /**
    * @param serializedDataCopy {Object} Object containing the Serialized Data
    */
  construct: function(serializedDataCopy) {
    this.base(arguments);

    this.setSerializedData(serializedDataCopy);

    this._setLayout(new qx.ui.layout.VBox(5));

    this.__buildLayout();
  },

  events: {
    "addCollaborators": "qx.event.type.Data"
  },

  members: {
    __serializedDataCopy: null,

    _createChildControlImpl: function(id) {
      let control;
      switch (id) {
        case "intro-text":
          control = new qx.ui.basic.Label(this.tr("Select from the list below and click Share"));
          this._add(control);
          break;
        case "buttons-layout":
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox());
          this._add(control);
          break;
        case "share-with":
          control = new qx.ui.form.Button(this.tr("Share with...")).set({
            appearance: "form-button",
            alignX: "left",
            allowGrowX: false
          });
          this.getChildControl("buttons-layout").add(control);
          this.getChildControl("buttons-layout").add(new qx.ui.core.Spacer(), {
            flex: 1
          });
          break;
        case "my-organizations":
          control = new qx.ui.form.Button(this.tr("My Organizations...")).set({
            appearance: "form-button-outlined",
            allowGrowY: false,
            allowGrowX: false,
            alignX: "right",
            icon: osparc.dashboard.CardBase.SHARED_ORGS
          });
          this.getChildControl("buttons-layout").add(control);
          break;
      }
      return control || this.base(arguments, id);
    },

    setSerializedData: function(serializedDataCopy) {
      this.__serializedDataCopy = serializedDataCopy;
    },

    __buildLayout: function() {
      this.getChildControl("intro-text");

      const addCollaboratorBtn = this.getChildControl("share-with");
      addCollaboratorBtn.addListener("execute", () => {
        const collaboratorsManager = new osparc.share.NewCollaboratorsManager(this.__serializedDataCopy);
        collaboratorsManager.addListener("addCollaborators", e => {
          collaboratorsManager.close();
          this.fireDataEvent("addCollaborators", e.getData());
        }, this);
      }, this);

      const organizations = this.getChildControl("my-organizations");
      organizations.addListener("execute", () => osparc.desktop.organizations.OrganizationsWindow.openWindow(), this);
    }
  }
});
