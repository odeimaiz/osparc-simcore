/* eslint no-warning-comments: "off" */

qx.Class.define("qxapp.data.model.WorkbenchModel", {
  extend: qx.core.Object,

  construct: function(wbData) {
    this.base(arguments);

    this.__nodesTopLevel = {};
    this.createNodeModels(wbData);
    this.createLinks(wbData);
  },

  events: {
    "WorkbenchModelChanged": "qx.event.type.Event"
  },

  members: {
    __nodesTopLevel: null,

    isContainer: function() {
      return false;
    },

    getNodeModel: function(nodeId) {
      const allNodes = this.getNodeModels(true);
      const exists = Object.prototype.hasOwnProperty.call(allNodes, nodeId);
      if (exists) {
        return allNodes[nodeId];
      }
      return null;
    },

    getNodeModels: function(recursive = false) {
      let nodes = Object.assign({}, this.__nodesTopLevel);
      if (recursive) {
        for (const nodeId in this.__nodesTopLevel) {
          let innerNodes = this.__nodesTopLevel[nodeId].getInnerNodes(true);
          nodes = Object.assign(nodes, innerNodes);
        }
      }
      return nodes;
    },

    createNodeModel: function(metaData, uuid, nodeData) {
      let existingNodeModel = this.getNodeModel(uuid);
      if (existingNodeModel) {
        return existingNodeModel;
      }
      let nodeModel = new qxapp.data.model.NodeModel(metaData, uuid);
      nodeModel.populateNodeData(nodeData);
      return nodeModel;
    },

    createNodeModels: function(workbenchData) {
      let keys = Object.keys(workbenchData);
      for (let i=0; i<keys.length; i++) {
        const nodeId = keys[i];
        const nodeData = workbenchData[nodeId];
        if ("parent" in nodeData) {
          let parentNode = this.getNodeModel(nodeData.parent);
          if (parentNode === null) {
            // If parent was not yet created, delay the creation of its' children
            keys.push(nodeId);
            // check if there is an inconsitency
            const nKeys = keys.length;
            if (nKeys > 1) {
              if (keys[nKeys-1] === keys[nKeys-2]) {
                console.log(nodeId, "will never be created, parent missing", nodeData.parent);
                return;
              }
            }
            continue;
          }
        }
        let nodeModel = null;
        if ("key" in nodeData) {
          // not container
          let store = qxapp.data.Store.getInstance();
          let metaData = store.getNodeMetaData(nodeData);
          nodeModel = this.createNodeModel(metaData, nodeId, nodeData);
        } else {
          // container
          nodeModel = this.createNodeModel(null, nodeId, nodeData);
        }
        if ("parent" in nodeData) {
          let parentModel = this.getNodeModel(nodeData.parent);
          this.addNodeModel(nodeModel, parentModel);
        } else {
          this.addNodeModel(nodeModel);
        }
      }
    },

    addNodeModel: function(nodeModel, parentNodeModel) {
      const uuid = nodeModel.getNodeId();
      if (parentNodeModel) {
        parentNodeModel.addInnerNode(uuid, nodeModel);
      } else {
        this.__nodesTopLevel[uuid] = nodeModel;
      }
      this.fireEvent("WorkbenchModelChanged");
    },

    removeNode: function(nodeModel) {
      // TODO: only works with top level nodes
      const nodeId = nodeModel.getNodeId();
      const exists = Object.prototype.hasOwnProperty.call(this.__nodesTopLevel, nodeId);
      if (exists) {
        if (nodeModel.getMetaData().type == "dynamic") {
          const slotName = "stopDynamic";
          let socket = qxapp.wrappers.WebSocket.getInstance();
          let data = {
            nodeId: nodeModel.getNodeId()
          };
          socket.emit(slotName, data);
        }
        delete this.__nodesTopLevel[nodeModel.getNodeId()];
        this.fireEvent("WorkbenchModelChanged");
      }
      return exists;
    },

    createLink: function(outputNodeId, inputNodeId) {
      let node = this.getNodeModel(inputNodeId);
      if (node) {
        node.addInputNode(outputNodeId);
      }
    },

    createLinks: function(workbenchData) {
      for (const nodeId in workbenchData) {
        const nodeData = workbenchData[nodeId];
        if (nodeData.inputNodes) {
          for (let i=0; i < nodeData.inputNodes.length; i++) {
            const outputNodeId = nodeData.inputNodes[i];
            this.createLink(outputNodeId, nodeId);
          }
        }
      }
    },

    removeLink: function(outputNodeId, inputNodeId) {
      let node = this.getNodeModel(inputNodeId);
      if (node) {
        return node.removeLink(outputNodeId);
      }
      return false;
    },

    serializeWorkbench: function(savePosition = false) {
      let workbench = {};
      for (const nodeId in this.getNodeModels()) {
        const nodeModel = this.getNodeModel(nodeId);
        const nodeData = nodeModel.getMetaData();
        // let cNode = workbench[nodeModel.getNodeId()] = {
        workbench[nodeModel.getNodeId()] = {
          key: nodeData.key,
          version: nodeData.version,
          inputs: nodeModel.getInputValues(),
          outputs: {}
        };
        /*
        if (savePosition && this.__desktop.indexOf(nodeModel)>-1) {
          cNode.position = {
            x: nodeModel.getPosition().x,
            y: nodeModel.getPosition().y
          };
        }
        for (let key in nodeData.outputs) {
          const outputPort = nodeData.outputs[key];
          if ("value" in outputPort) {
            cNode.outputs[key] = outputPort.value;
          }
        }
        */
      }
      return workbench;
    }
  }
});
