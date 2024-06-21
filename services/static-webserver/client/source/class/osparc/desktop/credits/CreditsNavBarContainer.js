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

qx.Class.define("osparc.desktop.credits.CreditsNavBarContainer", {
  extend: qx.ui.core.Widget,

  construct: function() {
    this.base(arguments);

    this._setLayout(new qx.ui.layout.Grow());

    this.set({
      zIndex: osparc.utils.Utils.FLOATING_Z_INDEX,
      maxWidth: 200,
      backgroundColor: "background-main-2",
      padding: 10
    });
    osparc.utils.Utils.setIdToWidget(this, "creditsNavBarContainer");

    const layout = new qx.ui.container.Composite(new qx.ui.layout.HBox(10));

    const creditsIndicator = new osparc.desktop.credits.CreditsIndicator();
    const store = osparc.store.Store.getInstance();
    store.bind("contextWallet", creditsIndicator, "wallet");
    layout.add(creditsIndicator, {
      flex: 1
    });

    const buttonSize = 24;
    const billingCenterButton = new qx.ui.form.Button().set({
      appearance: "form-button-outlined",
      width: buttonSize,
      height: buttonSize,
      alignX: "center",
      alignY: "middle",
      icon: "@FontAwesome5Solid/ellipsis-h/12"
    });
    // make it circular
    billingCenterButton.getContentElement().setStyles({
      "border-radius": `${buttonSize / 2}px`
    });
    billingCenterButton.addListener("execute", () => {
      osparc.desktop.credits.BillingCenterWindow.openWindow();
      this.exclude();
    });
    layout.add(billingCenterButton);

    this._add(layout);

    const root = qx.core.Init.getApplication().getRoot();
    root.add(this, {
      top: 0,
      right: 0
    });
  },

  members: {
    setPosition: function(x, y) {
      this.setLayoutProperties({
        left: x - osparc.notification.NotificationUI.MAX_WIDTH,
        top: y
      });
    }
  }
});
