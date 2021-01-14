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

qx.Class.define("osparc.component.task.TasksButton", {
  extend: qx.ui.core.Widget,

  construct: function() {
    this.base(arguments);

    this._setLayout(new qx.ui.layout.Canvas());

    this.set({
      width: 30,
      alignX: "center",
      cursor: "pointer"
    });

    this._createChildControlImpl("icon");
    this._createChildControlImpl("number");

    const tasks = osparc.component.task.Tasks.getInstance();
    tasks.getTasks().addListener("change", () => {
      this.__updateTasksButton();
    }, this);
    this.__updateTasksButton();

    this.addListener("tap", () => {
      this.__showTasks();
    }, this);
  },

  members: {
    __icon: null,
    __nTasks: null,

    _createChildControlImpl: function(id) {
      let control;
      switch (id) {
        case "icon": {
          control = new qx.ui.basic.Image("@FontAwesome5Solid/cog/24");

          const logoContainer = new qx.ui.container.Composite(new qx.ui.layout.HBox().set({
            alignY: "middle"
          }));
          logoContainer.add(control);

          this._add(logoContainer, {
            height: "100%"
          });
          break;
        }
        case "number":
          control = new qx.ui.basic.Label().set({
            font: "text-12"
          });
          this._add(control, {
            bottom: 3,
            right: 0
          });
          break;
      }
      return control || this.base(arguments, id);
    },

    __updateTasksButton: function() {
      const icon = this.getChildControl("icon");
      const number = this.getChildControl("number");

      const tasks = osparc.component.task.Tasks.getInstance();
      const nTasks = tasks.getTasks().length;
      number.setValue(nTasks.toString());
      if (nTasks) {
        this.show();
        icon.getContentElement().addClass("rotate");
      } else {
        this.exclude();
        icon.getContentElement().removeClass("rotate");
      }
    },

    __showTasks: function() {
      const bounds = this.getBounds();
      const tasks = osparc.component.task.Tasks.getInstance();
      tasks.setTasksContainerPosition(bounds.left, 50);
      tasks.getTasksContainer().show();
    },

    __hideTasks: function() {
      const tasks = osparc.component.task.Tasks.getInstance();
      tasks.getTasksContainer().exclude();
    }
  }
});
