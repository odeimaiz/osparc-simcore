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

qx.Class.define("osparc.navigation.UserMenuButton", {
  extend: qx.ui.form.MenuButton,

  construct: function() {
    this.base(arguments);

    const authData = osparc.auth.Data.getInstance();

    const menu = new osparc.navigation.UserMenu();
    osparc.utils.Utils.setIdToWidget(menu, "userMenuMenu");
    this.set({
      width: 40,
      height: 40,
      font: "text-14",
      allowShrinkX: false,
      allowShrinkY: false,
      allowGrowX: false,
      allowGrowY: false,
      menu
    });

    this.getContentElement().setStyles({
      "border-radius": "20px"
    });
    this.getChildControl("icon").getContentElement().setStyles({
      "border-radius": "16px"
    });
    osparc.utils.Utils.setIdToWidget(this, "userMenuBtn");

    const store = osparc.store.Store.getInstance();
    this.__bindWalletToHalo();
    store.addListener("changeContextWallet", () => this.__bindWalletToHalo());

    const userEmail = authData.getEmail() || "bizzy@itis.ethz.ch";
    const icon = this.getChildControl("icon");
    authData.bind("role", this, "icon", {
      converter: role => {
        if (["anonymous", "guest"].includes(role)) {
          icon.getContentElement().setStyles({
            "margin-left": "0px"
          });
          return "@FontAwesome5Solid/user-secret/28";
        }
        icon.getContentElement().setStyles({
          "margin-left": "-4px"
        });
        return osparc.utils.Avatar.getUrl(userEmail, 32);
      }
    });
  },

  statics: {
    openPreferences: function() {
      const preferencesWindow = osparc.desktop.preferences.PreferencesWindow.openWindow();
      return preferencesWindow;
    }
  },

  members: {
    __bindWalletToHalo: function() {
      const store = osparc.store.Store.getInstance();
      const contextWallet = store.getContextWallet();
      if (contextWallet) {
        this.__updateHalloCredits(contextWallet.getCreditsAvailable());
        contextWallet.addListener("changeCreditsAvailable", e => this.__updateHalloCredits(e.getData()));
      }
    },

    __updateHalloCredits: function(credits) {
      if (credits !== null) {
        const progress = osparc.desktop.credits.Utils.normalizeCredits(credits);
        const creditsColor = osparc.desktop.credits.Utils.creditsToColor(credits, "strong-main");
        const color1 = qx.theme.manager.Color.getInstance().resolve(creditsColor);
        const textColor = qx.theme.manager.Color.getInstance().resolve("text");
        const arr = qx.util.ColorUtil.stringToRgb(textColor);
        arr[3] = 0.5;
        const color2 = qx.util.ColorUtil.rgbToRgbString(arr);
        this.getContentElement().setStyles({
          "background": `radial-gradient(closest-side, white 79%, transparent 80% 100%), conic-gradient(${color1} ${progress}%, ${color2} 0)`
        });
      }
    },

    populateMenu: function() {
      this.getMenu().populateMenu();
    },

    populateMenuCompact: function() {
      this.getMenu().populateMenuCompact();
    }
  }
});
