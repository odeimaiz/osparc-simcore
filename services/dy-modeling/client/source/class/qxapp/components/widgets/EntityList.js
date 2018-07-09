/* eslint no-warning-comments: "off" */
/* eslint no-underscore-dangle: ["error", { "allowAfterThis": true, "enforceInMethodNames": true, "allow": ["__widgetChildren"] }] */

qx.Class.define("qxapp.components.widgets.EntityList", {
  extend: qx.ui.core.Widget,

  include: [qx.locale.MTranslation],

  construct: function() {
    this.base(arguments);

    let entityListLayout = new qx.ui.layout.VBox();
    this._setLayout(entityListLayout);

    let scroller = new qx.ui.container.Scroll();
    this._add(scroller, {
      flex: 1
    });

    // create and add the tree
    this.__tree = new qx.ui.tree.Tree();
    this.__tree.setSelectionMode("multi");

    let root = new qx.ui.tree.TreeFolder("Model");
    root.setOpen(true);
    this.__tree.setRoot(root);

    this.__tree.addListener("changeSelection", this.__onSelectionChanged.bind(this));

    let removeBtn = new qx.ui.form.Button(this.tr("Remove entity"));
    removeBtn.addListener("execute", this.__removeEntityPressed.bind(this));

    scroller.add(this.__tree);
    this._add(removeBtn);
  },

  events: {
    "removeEntityRequested": "qx.event.type.Data",
    "selectionChanged": "qx.event.type.Data",
    "visibilityChanged": "qx.event.type.Data"
  },

  members: {
    __tree: null,

    setBackgroudColor: function(color) {
      this.__tree.setBackgroundColor(color);
    },

    setTextColor: function(color) {
      this.__tree.setTextColor(color);
    },

    __onSelectionChanged: function(e) {
      let selectedIds = [];
      for (let i = 0; i < e.getData().length; i++) {
        selectedIds.push(e.getData()[i].id);
      }
      this.fireDataEvent("selectionChanged", selectedIds);
    },

    __removeEntityPressed: function() {
      let selectedIds = this.getSelectedEntityIds();
      for (let i = 0; i < selectedIds.length; i++) {
        this.fireDataEvent("removeEntityRequested", selectedIds[i]);
      }
    },

    __getSelectedEntities: function() {
      return this.__tree.getSelection();
    },

    getSelectedEntityId: function() {
      if (this.__getSelectedEntities().length > 0) {
        return this.__getSelectedEntities()[0].id;
      }
      return null;
    },

    getSelectedEntityIds: function() {
      let selectedIds = [];
      for (let i = 0; i < this.__getSelectedEntities().length; i++) {
        selectedIds.push(this.__getSelectedEntities()[i].id);
      }
      return selectedIds;
    },

    addEntity: function(id, name) {
      let newItem = new qx.ui.tree.TreeFile();

      // A checkbox comes right after the tree icon
      let checkbox = new qx.ui.form.CheckBox();
      checkbox.setFocusable(false);
      checkbox.setValue(true);
      newItem.addWidget(checkbox);
      checkbox.addListener("changeValue", function(e) {
        this.fireDataEvent("visibilityChanged", [id, e.getData()]);
        let selectedIds = this.getSelectedEntityIds();
        for (let i = 0; i < this.__tree.getRoot().getChildren().length; i++) {
          if (selectedIds.indexOf(this.__tree.getRoot().getChildren()[i].id) >= 0) {
            // ToDo: Look for a better solution
            for (let j = 0; j < this.__tree.getRoot().getChildren()[i].__widgetChildren.length; j++) {
              if (this.__tree.getRoot().getChildren()[i].__widgetChildren[j].basename === "CheckBox") {
                this.__tree.getRoot().getChildren()[i].__widgetChildren[j].setValue(e.getData());
              }
            }
          }
        }
      }, this);

      newItem.addLabel(name);

      newItem.id = id;
      this.__tree.getRoot().add(newItem);
      this.__tree.setSelection([newItem]);
    },

    removeEntity: function(uuid) {
      for (let i = 0; i < this.__tree.getRoot().getChildren().length; i++) {
        if (this.__tree.getRoot().getChildren()[i].id === uuid) {
          this.__tree.getRoot().remove(this.__tree.getRoot().getChildren()[i]);
        }
      }
    },

    onEntitySelectedChanged: function(uuids) {
      if (uuids === null) {
        this.__tree.resetSelection();
      } else {
        let selected = [];
        for (let i = 0; i < this.__tree.getRoot().getChildren().length; i++) {
          if (uuids.indexOf(this.__tree.getRoot().getChildren()[i].id) >= 0) {
            selected.push(this.__tree.getRoot().getChildren()[i]);
          }
        }
        this.__tree.setSelection(selected);
      }
    }
  }
});
