/* ************************************************************************

   osparc - the simcore frontend

   https://osparc.io

   Copyright:
     2020 IT'IS Foundation, https://itis.swiss

   License:
     MIT: https://opensource.org/licenses/MIT

   Authors:
     * Odei Maiz (odeimaiz)

************************************************************************ */

qx.Class.define("osparc.pricing.UnitEditor", {
  extend: qx.ui.core.Widget,

  construct: function(pricingPlanId, pricingUnit) {
    this.base(arguments);

    this._setLayout(new qx.ui.layout.VBox(10));

    this.__validator = new qx.ui.form.validation.Manager();

    this.set({
      pricingPlanId
    });

    if (pricingUnit) {
      this.set({
        pricingUnitId: pricingUnit.getPricingUnitId(),
        unitName: pricingUnit.getName(),
        costPerUnit: pricingUnit.getCost(),
        default: pricingUnit.getIsDefault(),
      });
      if (pricingUnit.getClassification() === "TIER") {
        this.set({
          specificInfo: pricingUnit.getSpecificInfo() && pricingUnit.getSpecificInfo()["aws_ec2_instances"] ? pricingUnit.getSpecificInfo()["aws_ec2_instances"].toString() : "",
        });
        const extraInfo = osparc.utils.Utils.deepCloneObject(pricingUnit.getExtraInfo());
        // extract the required fields from the unitExtraInfo
        this.set({
          unitExtraInfoCPU: extraInfo["CPU"],
          unitExtraInfoRAM: extraInfo["RAM"],
          unitExtraInfoVRAM: extraInfo["VRAM"]
        });
        delete extraInfo["CPU"];
        delete extraInfo["RAM"];
        delete extraInfo["VRAM"];
        this.set({
          unitExtraInfo: extraInfo
        });
      } else if (pricingUnit.getClassification() === "LICENSE") {
        this.set({
          // unitExtraInfoNSeats: pricingUnit.getNumberOfSeats(),
          unitExtraInfoNSeats: 42,
        });
      }
      this.getChildControl("save");
    } else {
      this.getChildControl("create");
    }
  },

  properties: {
    pricingPlanId: {
      check: "Number",
      init: null,
      nullable: false,
      apply: "__applyPricingPlanId"
    },

    pricingUnitId: {
      check: "Number",
      nullable: true,
      init: null,
      event: "changePricingUnitId"
    },

    unitName: {
      check: "String",
      init: "",
      nullable: false,
      event: "changeUnitName"
    },

    costPerUnit: {
      check: "Number",
      init: 0,
      nullable: false,
      event: "changeCostPerUnit"
    },

    comment: {
      check: "String",
      init: "",
      nullable: false,
      event: "changeComment"
    },

    specificInfo: {
      check: "String",
      init: null,
      nullable: true,
      event: "changeSpecificInfo"
    },

    unitExtraInfoCPU: {
      check: "Number",
      init: 0,
      nullable: false,
      event: "changeUnitExtraInfoCPU"
    },

    unitExtraInfoRAM: {
      check: "Number",
      init: 0,
      nullable: false,
      event: "changeUnitExtraInfoRAM"
    },

    unitExtraInfoVRAM: {
      check: "Number",
      init: 0,
      nullable: false,
      event: "changeUnitExtraInfoVRAM"
    },

    unitExtraInfo: {
      check: "Object",
      init: {},
      nullable: false,
      event: "changeUnitExtraInfo"
    },

    unitExtraInfoNSeats: {
      check: "Number",
      init: 1,
      nullable: false,
      event: "changeUnitExtraInfoNSeats"
    },

    default: {
      check: "Boolean",
      init: true,
      nullable: false,
      event: "changeDefault"
    }
  },

  events: {
    "done": "qx.event.type.Event",
    "cancel": "qx.event.type.Event"
  },

  members: {
    __validator: null,

    _createChildControlImpl: function(id) {
      let control;
      switch (id) {
        case "unit-form": {
          control = new qx.ui.form.Form();
          const formRenderer = new qx.ui.form.renderer.Single(control);
          this._add(formRenderer);
          break;
        }
        case "unit-name":
          control = new qx.ui.form.TextField().set({
            font: "text-14"
          });
          control.setRequired(true);
          this.__validator.add(control);
          this.bind("unitName", control, "value");
          control.bind("value", this, "unitName");
          this.getChildControl("unit-form").add(control, this.tr("Unit Name"));
          break;
        case "cost-per-unit":
          control = new qx.ui.form.Spinner().set({
            minimum: 0,
            maximum: 10000
          });
          control.setRequired(true);
          this.__validator.add(control);
          this.bind("costPerUnit", control, "value");
          control.bind("value", this, "costPerUnit");
          this.getChildControl("unit-form").add(control, this.tr("Cost per unit"));
          break;
        case "comment":
          control = new qx.ui.form.TextField().set({
            font: "text-14"
          });
          this.bind("comment", control, "value");
          control.bind("value", this, "comment");
          this.getChildControl("unit-form").add(control, this.tr("Comment"));
          break;
        case "specific-info": {
          control = new qx.ui.form.TextArea().set({
            font: "text-14"
          });
          this.__validator.add(control);
          this.bind("specificInfo", control, "value");
          control.bind("value", this, "specificInfo");
          this.getChildControl("unit-form").add(control, this.tr("Specific info"));
          break;
        }
        case "unit-extra-info-cpu": {
          control = new qx.ui.form.Spinner().set({
            minimum: 0,
            maximum: 10000
          });
          control.setRequired(true);
          this.bind("unitExtraInfoCPU", control, "value");
          control.bind("value", this, "unitExtraInfoCPU");
          this.getChildControl("unit-form").add(control, this.tr("CPU"));
          break;
        }
        case "unit-extra-info-ram": {
          control = new qx.ui.form.Spinner().set({
            minimum: 0,
            maximum: 10000
          });
          control.setRequired(true);
          this.bind("unitExtraInfoRAM", control, "value");
          control.bind("value", this, "unitExtraInfoRAM");
          this.getChildControl("unit-form").add(control, this.tr("RAM"));
          break;
        }
        case "unit-extra-info-vram": {
          control = new qx.ui.form.Spinner().set({
            minimum: 0,
            maximum: 10000
          });
          control.setRequired(true);
          this.bind("unitExtraInfoVRAM", control, "value");
          control.bind("value", this, "unitExtraInfoVRAM");
          this.getChildControl("unit-form").add(control, this.tr("VRAM"));
          break;
        }
        case "unit-extra-info": {
          control = new qx.ui.form.TextField().set({
            font: "text-14"
          });
          control.setRequired(true);
          this.__validator.add(control);
          this.bind("unitExtraInfo", control, "value", {
            converter: v => JSON.stringify(v)
          });
          control.bind("value", this, "unitExtraInfo", {
            converter: v => JSON.parse(v)
          });
          this.getChildControl("unit-form").add(control, this.tr("More Extra Info"));
          break;
        }
        case "unit-extra-info-n-seats": {
          control = new qx.ui.form.Spinner().set({
            minimum: 1,
            maximum: 10000
          });
          this.bind("unitExtraInfoNSeats", control, "value");
          control.bind("value", this, "unitExtraInfoNSeats");
          this.getChildControl("unit-form").add(control, this.tr("Number of Seats"));
          break;
        }
        case "is-default": {
          control = new qx.ui.form.CheckBox().set({
            value: true
          });
          this.bind("default", control, "value");
          control.bind("value", this, "default");
          this.getChildControl("unit-form").add(control, this.tr("Default"));
          break;
        }
        case "buttonsLayout": {
          control = new qx.ui.container.Composite(new qx.ui.layout.HBox(8).set({
            alignX: "right"
          }));
          const cancelButton = new qx.ui.form.Button(this.tr("Cancel")).set({
            appearance: "form-button-text"
          });
          cancelButton.addListener("execute", () => this.fireEvent("cancel"), this);
          control.addAt(cancelButton, 0);
          this._add(control);
          break;
        }
        case "create": {
          const buttons = this.getChildControl("buttonsLayout");
          control = new osparc.ui.form.FetchButton(this.tr("Create")).set({
            appearance: "form-button"
          });
          control.addListener("execute", () => {
            if (this.__validator.validate()) {
              control.setFetching(true);
              this.__createPricingUnit();
            }
          }, this);
          buttons.addAt(control, 1);
          break;
        }
        case "save": {
          const buttons = this.getChildControl("buttonsLayout");
          control = new osparc.ui.form.FetchButton(this.tr("Save")).set({
            appearance: "form-button"
          });
          control.addListener("execute", () => {
            if (this.__validator.validate()) {
              control.setFetching(true);
              this.__updatePricingUnit();
            }
          }, this);
          buttons.addAt(control, 1);
          break;
        }
      }

      return control || this.base(arguments, id);
    },

    __applyPricingPlanId: function(pricingPlanId) {
      const pricingPlan = osparc.store.Pricing.getInstance().getPricingPlan(pricingPlanId);
      if (pricingPlan) {
        this.getChildControl("unit-name");
        this.getChildControl("cost-per-unit");
        this.getChildControl("comment");
        if (pricingPlan.getClassification() === "TIER") {
          this.getChildControl("specific-info");
          this.getChildControl("unit-extra-info-cpu");
          this.getChildControl("unit-extra-info-ram");
          this.getChildControl("unit-extra-info-vram");
          this.getChildControl("unit-extra-info");
        } else if (pricingPlan.getClassification() === "LICENSE") {
          this.getChildControl("unit-extra-info-n-seats");
        }
        this.getChildControl("is-default");
      }
    },

    __createPricingUnit: function() {
      const data = {};
      data["unitName"] = this.getUnitName();
      data["costPerUnit"] = this.getCostPerUnit();
      data["comment"] = this.getComment();

      const pricingPlan = osparc.store.Pricing.getInstance().getPricingPlan(this.getPricingPlanId());
      if (pricingPlan) {
        if (pricingPlan.getClassification() === "TIER") {
          const awsEc2Instances = [];
          const specificInfo = this.getSpecificInfo();
          if (specificInfo) {
            awsEc2Instances.push(specificInfo);
          }
          data["specificInfo"] = {
            "aws_ec2_instances": awsEc2Instances
          };
          const extraInfo = {};
          extraInfo["CPU"] = this.getUnitExtraInfoCPU();
          extraInfo["RAM"] = this.getUnitExtraInfoRAM();
          extraInfo["VRAM"] = this.getUnitExtraInfoVRAM();
          Object.assign(extraInfo, this.getUnitExtraInfo());
          data["unitExtraInfo"] = extraInfo;
        } else if (pricingPlan.getClassification() === "LICENSE") {
          data["nSeats"] = this.getUnitExtraInfoNSeats();
        }
      }

      data["default"] = this.getDefault();
      const params = {
        url: {
          "pricingPlanId": this.getPricingPlanId()
        },
        data
      };
      osparc.data.Resources.fetch("pricingUnits", "post", params)
        .then(() => {
          osparc.FlashMessenger.getInstance().logAs(this.tr("Successfully created"));
          this.fireEvent("done");
        })
        .catch(err => {
          osparc.FlashMessenger.getInstance().logAs(this.tr("Something went wrong"), "ERROR");
          console.error(err);
        })
        .finally(() => this.getChildControl("create").setFetching(false));
    },

    __updatePricingUnit: function() {
      const unitName = this.getUnitName();
      const costPerUnit = this.getCostPerUnit();
      const comment = this.getComment();
      const specificInfo = this.getSpecificInfo();
      const extraInfo = {};
      extraInfo["CPU"] = this.getUnitExtraInfoCPU();
      extraInfo["RAM"] = this.getUnitExtraInfoRAM();
      extraInfo["VRAM"] = this.getUnitExtraInfoVRAM();
      Object.assign(extraInfo, this.getUnitExtraInfo());
      const isDefault = this.getDefault();

      const params = {
        url: {
          "pricingPlanId": this.getPricingPlanId(),
          "pricingUnitId": this.getPricingUnitId()
        },
        data: {
          "unitName": unitName,
          "pricingUnitCostUpdate": {
            "cost_per_unit": costPerUnit,
            "comment": comment
          },
          "specificInfo": {
            "aws_ec2_instances": [specificInfo]
          },
          "unitExtraInfo": extraInfo,
          "default": isDefault
        }
      };
      osparc.data.Resources.fetch("pricingUnits", "update", params)
        .then(() => {
          osparc.FlashMessenger.getInstance().logAs(this.tr("Successfully updated"));
          this.fireEvent("done");
        })
        .catch(err => {
          osparc.FlashMessenger.getInstance().logAs(this.tr("Something went wrong"), "ERROR");
          console.error(err);
        })
        .finally(() => this.getChildControl("save").setFetching(false));
    }
  }
});
