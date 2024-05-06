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

qx.Class.define("osparc.dashboard.NewStudies", {
  extend: qx.ui.core.Widget,

  construct: function(newStudies) {
    this.base(arguments);

    this.__newStudies = newStudies;

    this._setLayout(new qx.ui.layout.VBox(10));

    this.__newStudies = [];

    const flatList = this.__flatList = new osparc.dashboard.ToggleButtonContainer();
    [
      "changeSelection",
      "changeVisibility"
    ].forEach(signalName => {
      flatList.addListener(signalName, e => this.fireDataEvent(signalName, e.getData()), this);
    });
    this._add(this.__flatList);

    this.__groupedContainers = [];
  },

  properties: {
    mode: {
      check: ["grid", "list"],
      init: "grid",
      nullable: false,
      event: "changeMode",
      apply: "reloadCards"
    },

    groupBy: {
      check: [null, "category"],
      init: null,
      nullable: true
    }
  },

  events: {
    "newStudyClicked": "qx.event.type.Data"
  },

  members: {
    __newStudies: null,
    __flatList: null,
    __groupedContainers: null,

    reloadCards: function(listId) {
      this.__cleanAll();

      if (this.getGroupBy()) {
        const noGroupContainer = this.__createGroupContainer("no-group", "No Group", "transparent");
        this._add(noGroupContainer);
      } else {
        const flatList = this.__flatList = new osparc.dashboard.ToggleButtonContainer();
        osparc.utils.Utils.setIdToWidget(flatList, listId);
        [
          "changeSelection",
          "changeVisibility"
        ].forEach(signalName => {
          flatList.addListener(signalName, e => this.fireDataEvent(signalName, e.getData()), this);
        });
        const spacing = this.getMode() === "grid" ? osparc.dashboard.GridButtonBase.SPACING : osparc.dashboard.ListButtonBase.SPACING;
        this.__flatList.getLayout().set({
          spacingX: spacing,
          spacingY: spacing
        });
        this._add(this.__flatList);
      }

      let cards = [];
      this.__newStudies.forEach(resourceData => {
        Array.prototype.push.apply(cards, this.__resourceToCards(resourceData));
      });
      return cards;
    },

    __resourceToCards: function(resourceData) {
      const cards = [];
      if (this.getGroupBy() === "category") {
        this.__groupByCategory(cards, resourceData);
      } else {
        const card = this.__createCard(resourceData);
        cards.push(card);
        this.__flatList.add(card);
      }
      return cards;
    },

    __groupByCategory: function(cards, resourceData) {
      const categories = resourceData.tags ? osparc.store.Store.getInstance().getTags().filter(tag => resourceData.tags.includes(tag.id)) : [];
      if (categories.length === 0) {
        let noGroupContainer = this.__getGroupContainer("no-group");
        const card = this.__createCard(resourceData);
        noGroupContainer.add(card);
        cards.push(card);
      } else {
        categories.forEach(tag => {
          let groupContainer = this.__getGroupContainer(tag.id);
          if (groupContainer === null) {
            groupContainer = this.__createGroupContainer(tag.id, tag.name, tag.color);
            this._add(groupContainer);
            this._getChildren().sort((a, b) => a.getHeaderLabel().localeCompare(b.getHeaderLabel()));
            this.__moveNoGroupToLast();
          }
          const card = this.__createCard(resourceData);
          groupContainer.add(card);
          cards.push(card);
        });
      }
    },

    __createGroupContainer: function(groupId, headerLabel, headerColor = "text") {
      const groupContainer = new osparc.dashboard.GroupedToggleButtonContainer().set({
        groupId: groupId.toString(),
        headerLabel,
        headerIcon: "",
        headerColor,
        visibility: "excluded"
      });
      this.__groupedContainers.push(groupContainer);
      return groupContainer;
    },

    __getGroupContainer: function(gid) {
      const idx = this.__groupedContainers.findIndex(groupContainer => groupContainer.getGroupId() === gid.toString());
      if (idx > -1) {
        return this.__groupedContainers[idx];
      }
      return null;
    },

    __createCard: function(templateInfo) {
      const title = templateInfo.title;
      const desc = templateInfo.description;
      const mode = this.getMode();
      const newPlanButton = (mode === "grid") ? new osparc.dashboard.GridButtonNew(title, desc) : new osparc.dashboard.ListButtonNew(title, desc);
      newPlanButton.setCardKey(templateInfo.idToWidget);
      osparc.utils.Utils.setIdToWidget(newPlanButton, templateInfo.idToWidget);
      if (this.getMode() === "list") {
        const width = this.getBounds().width - 15;
        newPlanButton.setWidth(width);
      }
      return newPlanButton;
    },

    __cleanAll: function() {
      if (this.__flatList) {
        this.__flatList.removeAll();
        this.__flatList = null;
      }
      this.__groupedContainers.forEach(groupedContainer => groupedContainer.getContentContainer().removeAll());
      this.__groupedContainers = [];
      this._removeAll();
    },

    __moveNoGroupToLast: function() {
      const idx = this._getChildren().findIndex(grpContainer => grpContainer === this.__getGroupContainer("no-group"));
      if (idx > -1) {
        this._getChildren().push(this._getChildren().splice(idx, 1)[0]);
      }
    }
  }
});
