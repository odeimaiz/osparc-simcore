/* ************************************************************************

   osparc - the simcore frontend

   https://osparc.io

   Copyright:
     2019 IT'IS Foundation, https://itis.swiss

   License:
     MIT: https://opensource.org/licenses/MIT

   Authors:
     * Odei Maiz (odeimaiz)

************************************************************************ */

/**
 * Base class for NodeInput and NodeOutput
 */

qx.Class.define("osparc.component.widget.NodeInOut", {
  extend: qx.ui.core.Widget,

  /**
    * @param node {osparc.data.model.Node} Node owning the widget
  */
  construct: function(node) {
    this.setNode(node);

    this.base();

    let nodeInOutLayout = new qx.ui.layout.VBox(10);
    this._setLayout(nodeInOutLayout);

    this.set({
      decorator: "main"
    });
  },

  properties: {
    node: {
      check: "osparc.data.model.Node",
      nullable: false
    },

    inputPort: {
      init: null,
      nullable: true
    },

    outputPort: {
      init: null,
      nullable: true
    }
  },

  events: {
    "edgeDragStart": "qx.event.type.Data",
    "edgeDragOver": "qx.event.type.Data",
    "edgeDrop": "qx.event.type.Data",
    "edgeDragEnd": "qx.event.type.Data"
  },

  members: {
    getNodeId: function() {
      return this.getNode().getNodeId();
    },

    getMetaData: function() {
      return this.getNode().getMetaData();
    },

    emptyPorts: function() {
      this.setInputPort(null);
      this.setOutputPort(null);
    },

    getEdgePoint: function(port) {
      const nodeBounds = this.getCurrentBounds();
      if (nodeBounds === null) {
        // not rendered yet
        return null;
      }
      const x = port.isInput ? null : 0;
      const y = nodeBounds.top + nodeBounds.height/2;
      return [x, y];
    },

    getCurrentBounds: function() {
      let bounds = this.getBounds();
      let cel = this.getContentElement();
      if (cel) {
        let domeEle = cel.getDomElement();
        if (domeEle) {
          bounds.left = parseInt(domeEle.style.left);
          bounds.top = parseInt(domeEle.style.top);
        }
      }
      return bounds;
    },

    _getInputNodes: function() {
      const study = osparc.store.Store.getInstance().getCurrentStudy();
      const workbench = study.getWorkbench();
      const inputNodes = [];
      const inputNodeIds = this.getNode().getInputNodes();
      inputNodeIds.forEach(inputNodeId => {
        inputNodes.push(workbench.getNode(inputNodeId));
      });
      return inputNodes;
    },

    _getOutputNodes: function() {
      const study = osparc.store.Store.getInstance().getCurrentStudy();
      const workbench = study.getWorkbench();
      const outputNodes = [];
      const outputNodeIds = this.getNode().getOutputNodes();
      outputNodeIds.forEach(outputNodeId => {
        outputNodes.push(workbench.getNode(outputNodeId));
      });
      return outputNodes;
    },

    _createUIPorts: function(isInput, ports) {
      // Always create ports if node is a container
      if (!this.getNode().isContainer() && Object.keys(ports).length < 1) {
        return;
      }
      this.__createUIPortConnections(this, isInput);
      let label = {
        isInput: isInput,
        ui: this
      };
      label.ui.isInput = isInput;
      isInput ? this.setInputPort(label) : this.setOutputPort(label);
    },

    __createUIPortConnections: function(uiPort, isInput) {
      [
        ["dragstart", "edgeDragStart"],
        ["dragover", "edgeDragOver"],
        ["drop", "edgeDrop"],
        ["dragend", "edgeDragEnd"]
      ].forEach(eventPair => {
        uiPort.addListener(eventPair[0], e => {
          const eData = {
            event: e,
            nodeId: this.getNodeId(),
            isInput: isInput
          };
          this.fireDataEvent(eventPair[1], eData);
        }, this);
      }, this);
    }
  }
});
