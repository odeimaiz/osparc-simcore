/* ************************************************************************

   osparc - the simcore frontend

   https://osparc.io

   Copyright:
     2018 IT'IS Foundation, https://itis.swiss

   License:
     MIT: https://opensource.org/licenses/MIT

   Authors:
     * Odei Maiz (odeimaiz)

************************************************************************ */

/**
 * @asset(jsondiffpatch/jsondiffpatch.*js)
 * @ignore(jsondiffpatch)
 */

/* global jsondiffpatch */

/**
 * A qooxdoo wrapper for
 * <a href='https://github.com/benjamine/jsondiffpatch' target='_blank'>JsonDiffPatch</a>
 */

qx.Class.define("osparc.wrapper.JsonDiffPatch", {
  extend: qx.core.Object,
  type: "singleton",

  statics: {
    NAME: "jsondiffpatch",
    VERSION: "0.7.3",
    URL: "https://github.com/benjamine/jsondiffpatch"
  },

  construct: function() {
    this.base(arguments);
  },

  properties: {
    libReady: {
      nullable: false,
      init: false,
      check: "Boolean"
    }
  },

  members: {
    __diffPatcher: null,
    __deltaToPatch: null,

    init: function() {
      // initialize the script loading
      const jsondiffpatchPath = "jsondiffpatch/jsondiffpatch.min.js"; // own build required for the formatters to work
      const dynLoader = new qx.util.DynamicScriptLoader([
        jsondiffpatchPath
      ]);

      dynLoader.addListenerOnce("ready", e => {
        console.log(jsondiffpatchPath + " loaded");

        this.__diffPatcher = jsondiffpatch.create();

        const JsonPatchFormatter = jsondiffpatch.formatters.jsonpatch;
        this.__deltaToPatch = new JsonPatchFormatter();

        this.setLibReady(true);
      }, this);

      dynLoader.addListener("failed", e => {
        let data = e.getData();
        console.error("failed to load " + data.script);
      }, this);

      dynLoader.start();
    },

    // https://github.com/benjamine/jsondiffpatch/blob/master/docs/deltas.md
    diff: function(obj1, obj2) {
      let delta = this.__diffPatcher.diff(obj1, obj2);
      return delta;
    },

    // format to JSON PATCH (RFC 6902)
    // https://github.com/benjamine/jsondiffpatch/blob/master/docs/formatters.md
    deltaToJsonPatches: function(delta) {
      if (this.__deltaToPatch) {
        const patches = this.__deltaToPatch.format(delta);
        return patches;
      }
      return [];
    },
  }
});
