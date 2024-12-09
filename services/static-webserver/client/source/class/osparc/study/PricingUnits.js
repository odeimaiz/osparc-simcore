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

qx.Class.define("osparc.study.PricingUnits", {
  extend: qx.ui.container.Composite,

  construct: function(pricingUnitsData, preselectedPricingUnit, changeSelectionAllowed = true) {
    this.base(arguments);

    this.set({
      layout: new qx.ui.layout.HBox(5),
      allowGrowY: false,
    });

    this.__buildLayout(pricingUnitsData, preselectedPricingUnit, changeSelectionAllowed);
  },

  properties: {
    selectedUnitId: {
      check: "Number",
      init: null,
      nullable: false,
      event: "changeSelectedUnitId"
    }
  },

  members: {
    __buildLayout: function(pricingUnitsData, preselectedPricingUnit, changeSelectionAllowed) {
      const buttons = [];
      pricingUnitsData.forEach(pricingUnitData => {
        const pricingUnit = new osparc.data.model.PricingUnit(pricingUnitData);
        const button = new osparc.study.PricingUnitTier(pricingUnit).set({
          showSelectButton: changeSelectionAllowed,
        });
        buttons.push(button);
        this._add(button);
      });

      const groupOptions = new qx.ui.form.RadioGroup();
      buttons.forEach(btn => {
        groupOptions.add(btn);
        btn.bind("value", btn, "backgroundColor", {
          converter: selected => selected ? "background-main-1" : "transparent"
        });
      });

      if (preselectedPricingUnit) {
        const buttonFound = buttons.find(button => button.getUnitData().getPricingUnitId() === preselectedPricingUnit["pricingUnitId"]);
        if (buttonFound) {
          buttonFound.setValue(true);
        }
      } else {
        // preselect default
        buttons.forEach(button => {
          if (button.getUnitData().getIsDefault()) {
            button.setValue(true);
          }
        });
      }

      buttons.forEach(button => {
        if (!changeSelectionAllowed) {
          button.setCursor("default");
        }
        [
          "execute",
          "selectPricingUnit",
        ].forEach(ev => {
          button.addListener(ev, () => {
            if (changeSelectionAllowed) {
              const selectedUnitId = button.getUnitData().getPricingUnitId();
              this.setSelectedUnitId(selectedUnitId);
            } else {
              buttons.forEach(btn => btn.setValue(btn.getUnitData().getIsDefault()));
            }
          });
        });
      });
    }
  }
});
