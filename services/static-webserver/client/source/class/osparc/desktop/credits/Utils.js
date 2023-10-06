/* ************************************************************************

   osparc - the simcore frontend

   https://osparc.io

   Copyright:
     2023 IT'IS Foundation, https://itis.swiss

   License:
     MIT: https://opensource.org/licenses/MIT

   Authors:
     * Odei Maiz (odeimaiz)

************************************************************************ */

qx.Class.define("osparc.desktop.credits.Utils", {
  type: "static",

  statics: {
    areWalletsEnabled: function() {
      return new Promise(resolve => {
        Promise.all([
          osparc.utils.Utils.isDevelopmentPlatform(),
          osparc.utils.Utils.isStagingPlatform()
        ])
          .then(values => {
            const isDevel = values[0];
            const isStaging = values[1];
            if ((isDevel || isStaging) && (osparc.product.Utils.isProduct("s4l") || osparc.product.Utils.isProduct("s4lacad"))) {
              resolve(true);
            } else {
              resolve(false);
            }
          });
      });
    },

    creditsToFixed: function(credits) {
      if (credits < 100) {
        return credits.toFixed(1);
      }
      return parseInt(credits);
    },

    createWalletSelector: function(accessRight = "read", onlyActive = false, emptySelection = false) {
      const store = osparc.store.Store.getInstance();

      const walletSelector = new qx.ui.form.SelectBox();

      const populateSelectBox = selectBox => {
        selectBox.removeAll();

        const wallets = store.getWallets();
        if (emptySelection) {
          const sbItem = new qx.ui.form.ListItem(qx.locale.Manager.tr("Select Credit Account"));
          sbItem.walletId = null;
          selectBox.add(sbItem);
        }
        wallets.forEach(wallet => {
          if (onlyActive && wallet.getStatus() !== "ACTIVE") {
            return;
          }
          const found = wallet.getMyAccessRights();
          if (found && found[accessRight]) {
            const sbItem = new qx.ui.form.ListItem(wallet.getName());
            sbItem.walletId = wallet.getWalletId();
            selectBox.add(sbItem);
          }
        });
      };

      populateSelectBox(walletSelector);
      store.addListener("changeWallets", () => populateSelectBox(walletSelector));

      return walletSelector;
    },

    autoSelectActiveWallet: function(walletSelector) {
      // If there is only one active wallet, select it
      const store = osparc.store.Store.getInstance();
      const wallets = store.getWallets();
      const activeWallets = wallets.filter(wallet => wallet.getStatus() === "ACTIVE");
      if (activeWallets.length === 1) {
        const found = walletSelector.getSelectables().find(sbItem => sbItem.walletId === activeWallets[0].getWalletId());
        if (found) {
          walletSelector.setSelection([found]);
          return true;
        }
      }
      return false;
    },

    getWallet: function(walletId) {
      const store = osparc.store.Store.getInstance();
      const wallets = store.getWallets();
      const foundWallet = wallets.find(wallet => wallet.getWalletId() === walletId);
      if (foundWallet) {
        return foundWallet;
      }
      return null;
    },

    getPreferredWallet: function() {
      const store = osparc.store.Store.getInstance();
      const wallets = store.getWallets();
      const favouriteWallet = wallets.find(wallet => wallet.isPreferredWallet());
      if (favouriteWallet) {
        return favouriteWallet;
      }
      return null;
    }
  }
});
