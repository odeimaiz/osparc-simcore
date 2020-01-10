/*
 * oSPARC - The SIMCORE frontend - https://osparc.io
 * Copyright: 2019 IT'IS Foundation - https://itis.swiss
 * License: MIT - https://opensource.org/licenses/MIT
 * Authors: Ignacio Pascual (ignapas)
 *          Odei Maiz (odeimaiz)
 */

/**
 * Widget that contains the StudyDetails of the given study metadata.
 *
 * It also provides a button that opens a window with the same information.
 *
 * *Example*
 *
 * Here is a little example of how to use the widget.
 *
 * <pre class='javascript'>
 *    const serviceInfo = new osparc.component.metadata.ServiceInfo(selectedService);
 *    this.add(serviceInfo);
 * </pre>
 */

qx.Class.define("osparc.component.export.ExportMacro", {
  extend: qx.ui.core.Widget,

  /**
    * @param node {osparc.data.model.Node} Node owning the widget
    */
  construct: function(node) {
    this.base(arguments);

    this._setLayout(new qx.ui.layout.VBox(8));

    this.set({
      node
    });

    this.__buildLayout();
  },

  properties: {
    node: {
      check: "osparc.data.model.Node",
      nullable: false
    }
  },

  members: {
    __buildLayout: function() {
      this.__buildMetaDataForm();
      this.__buildInputSettings();
      this.__buildExposedSettings();
    },

    __buildMetaDataForm: function() {
      const metaDataForm = new qx.ui.form.Form();

      const serviceName = new qx.ui.form.TextField();
      serviceName.setRequired(true);
      metaDataForm.add(serviceName, this.tr("Name"));

      const serviceDesc = new qx.ui.form.TextField();
      metaDataForm.add(serviceDesc, this.tr("Description"));

      const formRenderer = new qx.ui.form.renderer.Single(metaDataForm).set({
        padding: 10
      });
      this._add(formRenderer);
    },

    __buildInputSettings: function() {
      console.log(this.getNode());
    },

    __buildExposedSettings: function() {
    }
  }
});
