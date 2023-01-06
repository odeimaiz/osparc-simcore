/* ************************************************************************

   osparc - the simcore frontend

   https://osparc.io

   Copyright:
     2018 IT'IS Foundation, https://itis.swiss

   License:
     MIT: https://opensource.org/licenses/MIT

   Authors:
     * Odei Maiz (odeimaiz)
     * Tobias Oetiker (oetiker)

************************************************************************ */

/* eslint "qx-rules/no-refs-in-members": "warn" */

/**
 * Widget used mainly by StudyBrowser for displaying Studies
 *
 * It consists of a thumbnail and creator and last change as caption
 */

qx.Class.define("osparc.dashboard.GridButtonItem", {
  extend: osparc.dashboard.GridButtonBase,

  construct: function() {
    this.base(arguments);

    this.setPriority(osparc.dashboard.CardBase.CARD_PRIORITY.ITEM);

    this.addListener("changeValue", this.__itemSelected, this);
  },

  statics: {
    MENU_BTN_WIDTH: 32
  },

  members: {
    // overridden
    _createChildControlImpl: function(id) {
      let control;
      switch (id) {
        case "tsr-rating": {
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox(2)).set({
            toolTipText: this.tr("Ten Simple Rules")
          });
          const tsrLabel = new qx.ui.basic.Label(this.tr("TSR:"));
          control.add(tsrLabel);
          const tsrRating = new osparc.ui.basic.StarsRating();
          control.add(tsrRating);
          this._mainLayout.add(control, osparc.dashboard.GridButtonBase.POS.TSR);
          break;
        }
        case "ui-mode": {
          control = new qx.ui.basic.Image().set({
            alignY: "middle"
          });
          this._mainLayout.add(control, osparc.dashboard.GridButtonBase.POS.VIEWER_MODE);
          break;
        }
        case "update-study": {
          control = new qx.ui.basic.Image().set({
            source: "@MaterialIcons/update/16",
            visibility: "excluded",
            alignY: "middle"
          });
          this._mainLayout.add(control, osparc.dashboard.GridButtonBase.POS.UPDATES);
          break;
        }
        case "hits-service": {
          control = new qx.ui.basic.Label().set({
            toolTipText: this.tr("Number of times it was instantiated"),
            alignY: "middle"
          });
          this._mainLayout.add(control, osparc.dashboard.GridButtonBase.POS.UPDATES);
          break;
        }
        case "tags":
          control = new qx.ui.container.Composite(new qx.ui.layout.Flow(5, 3)).set({
            anonymous: true
          });
          this._mainLayout.add(control, osparc.dashboard.GridButtonBase.POS.TAGS);
          break;
        case "menu-button": {
          this.getChildControl("title").set({
            maxWidth: osparc.dashboard.GridButtonBase.ITEM_WIDTH - 2*osparc.dashboard.GridButtonBase.PADDING - this.self().MENU_BTN_WIDTH
          });
          control = new qx.ui.form.MenuButton().set({
            width: this.self().MENU_BTN_WIDTH,
            height: this.self().MENU_BTN_WIDTH,
            icon: "@FontAwesome5Solid/ellipsis-v/14",
            focusable: false
          });
          osparc.utils.Utils.setIdToWidget(control, "studyItemMenuButton");
          this._add(control, {
            top: -2,
            right: -2
          });
          break;
        }
        case "tick-unselected":
          control = new qx.ui.basic.Image("@FontAwesome5Solid/circle/16");
          this._add(control, {
            top: 4,
            right: 4
          });
          break;
        case "tick-selected":
          control = new qx.ui.basic.Image("@FontAwesome5Solid/check-circle/16");
          this._add(control, {
            top: 4,
            right: 4
          });
          break;
        case "lock-status":
          control = new osparc.ui.basic.Thumbnail();
          this._add(control, {
            top: 0,
            right: 0,
            bottom: 0,
            left: 0
          });
          break;
        case "permission-icon": {
          control = new qx.ui.basic.Image();
          control.exclude();
          this._add(control, {
            bottom: 2,
            right: 2
          });
          break;
        }
      }

      return control || this.base(arguments, id);
    },

    // overridden
    _applyMultiSelectionMode: function(value) {
      if (value) {
        const menuButton = this.getChildControl("menu-button");
        menuButton.setVisibility("excluded");
        this.__itemSelected();
      } else {
        this.__showMenuOnly();
      }
    },

    __itemSelected: function() {
      if (this.isResourceType("study") && this.isMultiSelectionMode()) {
        const selected = this.getValue();

        if (this.isLocked() && selected) {
          this.setValue(false);
        }

        const tick = this.getChildControl("tick-selected");
        tick.setVisibility(selected ? "visible" : "excluded");

        const untick = this.getChildControl("tick-unselected");
        untick.setVisibility(selected ? "excluded" : "visible");
      } else {
        this.__showMenuOnly();
      }
    },

    __showMenuOnly: function() {
      const menuButton = this.getChildControl("menu-button");
      menuButton.setVisibility("visible");
      const tick = this.getChildControl("tick-selected");
      tick.setVisibility("excluded");
      const untick = this.getChildControl("tick-unselected");
      untick.setVisibility("excluded");
    },

    // overridden
    _applyLastChangeDate: function(value, old) {
      if (value && this.isResourceType("study")) {
        const label = this.getChildControl("subtitle-text");
        label.setValue(osparc.utils.Utils.formatDateAndTime(value));
      }
    },

    // overridden
    _applyOwner: function(value, old) {
      if (this.isResourceType("service") || this.isResourceType("template")) {
        const label = this.getChildControl("subtitle-text");
        if (value === osparc.auth.Data.getInstance().getEmail()) {
          label.setValue(this.tr("me"));
        } else {
          label.setValue(value);
        }
      }
    },

    _applyAccessRights: function(value, old) {
      if (value && Object.keys(value).length) {
        const sharedIcon = this.getChildControl("subtitle-icon");
        sharedIcon.addListener("tap", e => {
          e.stopPropagation();
          this._openAccessRights();
        }, this);
        sharedIcon.addListener("pointerdown", e => e.stopPropagation());

        const store = osparc.store.Store.getInstance();
        Promise.all([
          store.getGroupEveryone(),
          store.getVisibleMembers(),
          store.getGroupsOrganizations()
        ])
          .then(values => {
            const everyone = values[0];
            const orgMembs = [];
            const orgMembers = values[1];
            for (const gid of Object.keys(orgMembers)) {
              orgMembs.push(orgMembers[gid]);
            }
            const orgs = values.length === 3 ? values[2] : [];
            const groups = [orgMembs, orgs, [everyone]];
            this.__evaluateShareIcon(value, groups);
          });

        if (this.isResourceType("study")) {
          this._setStudyPermissions(value);
        }
      }
    },

    // groups sorted by [orgMembs, orgs, [everyone]];
    __evaluateShareIcon: function(value, groups) {
      const shareIcon = this.getChildControl("subtitle-icon");
      if (osparc.data.model.Study.canIWrite(value)) {
        shareIcon.set({
          source: osparc.dashboard.CardBase.SHARE_ICON,
          toolTipText: this.tr("Share")
        });
      }
      let sharedGrps = [];
      const myGroupId = osparc.auth.Data.getInstance().getGroupId();
      for (let i=0; i<groups.length; i++) {
        const sharedGrp = [];
        const gids = Object.keys(value);
        for (let j=0; j<gids.length; j++) {
          const gid = parseInt(gids[j]);
          if (this.isResourceType("study") && (gid === myGroupId)) {
            continue;
          }
          const grp = groups[i].find(group => group["gid"] === gid);
          if (grp) {
            sharedGrp.push(grp);
          }
        }
        if (sharedGrp.length === 0) {
          continue;
        } else {
          sharedGrps = sharedGrps.concat(sharedGrp);
        }
        switch (i) {
          case 0:
            shareIcon.setSource(osparc.dashboard.CardBase.SHARED_USER);
            break;
          case 1:
            shareIcon.setSource(osparc.dashboard.CardBase.SHARED_ORGS);
            break;
          case 2:
            shareIcon.setSource(osparc.dashboard.CardBase.SHARED_ALL);
            break;
        }
      }

      // tooltip
      if (sharedGrps.length === 0) {
        return;
      }
      const sharedGrpLabels = [];
      const maxItems = 6;
      for (let i=0; i<sharedGrps.length; i++) {
        if (i > maxItems) {
          sharedGrpLabels.push("...");
          break;
        }
        const sharedGrpLabel = sharedGrps[i]["label"];
        if (!sharedGrpLabels.includes(sharedGrpLabel)) {
          sharedGrpLabels.push(sharedGrpLabel);
        }
      }
      const hintText = sharedGrpLabels.join("<br>");
      const hint = new osparc.ui.hint.Hint(shareIcon, hintText);
      shareIcon.addListener("mouseover", () => hint.show(), this);
      shareIcon.addListener("mouseout", () => hint.exclude(), this);
    },

    _applyTags: function(tags) {
      if (osparc.data.Permissions.getInstance().canDo("study.tag")) {
        const tagsContainer = this.getChildControl("tags");
        tagsContainer.setVisibility(tags.length ? "visible" : "excluded");
        tagsContainer.removeAll();
        tags.forEach(tag => {
          const tagUI = new osparc.ui.basic.Tag(tag.name, tag.color, "searchBarFilter");
          tagUI.setFont("text-12");
          tagsContainer.add(tagUI);
        });
      }
    },

    // overridden
    _applyMenu: function(value, old) {
      const menuButton = this.getChildControl("menu-button");
      if (value) {
        menuButton.setMenu(value);
      }
      menuButton.setVisibility(value ? "visible" : "excluded");
    }
  }
});
