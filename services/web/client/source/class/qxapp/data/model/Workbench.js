/* ************************************************************************

   qxapp - the simcore frontend

   https://osparc.io

   Copyright:
     2018 IT'IS Foundation, https://itis.swiss

   License:
     MIT: https://opensource.org/licenses/MIT

   Authors:
     * Odei Maiz (odeimaiz)

************************************************************************ */

/**
 * Class that stores Workbench data.
 *
 * It takes care of creating, storing and managing nodes and links.
 *
 *                                    -> {NODES}
 * PROJECT -> METADATA + WORKBENCH ->|
 *                                    -> {LINKS}
 *
 * *Example*
 *
 * Here is a little example of how to use the widget.
 *
 * <pre class='javascript'>
 *   let link = new qxapp.data.model.Link(linkId, node1Id, node2Id);
 * </pre>
 */

qx.Class.define("qxapp.data.model.Workbench", {
  extend: qx.core.Object,

  /**
    * @param prjName {String} uuid if the link. If not provided, a random one will be assigned
    * @param wbData {String} uuid of the node where the link comes from
  */
  construct: function(prjName, wbData) {
    this.base(arguments);

    this.__nodesTopLevel = {};
    this.__links = {};

    this.setProjectName(prjName);
    this.__createNodes(wbData);
    this.__createLinks(wbData);
  },

  properties: {
    projectName: {
      check: "String",
      nullable: false
    }
  },

  events: {
    "workbenchChanged": "qx.event.type.Event",
    "updatePipeline": "qx.event.type.Data",
    "showInLogger": "qx.event.type.Data"
  },

  members: {
    __nodesTopLevel: null,
    __links: null,

    isContainer: function() {
      return false;
    },

    getNode: function(nodeId) {
      const allNodes = this.getNodes(true);
      const exists = Object.prototype.hasOwnProperty.call(allNodes, nodeId);
      if (exists) {
        return allNodes[nodeId];
      }
      return null;
    },

    getNodes: function(recursive = false) {
      let nodes = Object.assign({}, this.__nodesTopLevel);
      if (recursive) {
        let topLevelNodes = Object.values(this.__nodesTopLevel);
        for (const topLevelNode of topLevelNodes) {
          let innerNodes = topLevelNode.getInnerNodes(true);
          nodes = Object.assign(nodes, innerNodes);
        }
      }
      return nodes;
    },

    getPathIds: function(nodeId) {
      if (nodeId === "root" || nodeId === undefined) {
        return ["root"];
      }
      let nodePath = [];
      nodePath.unshift(nodeId);
      const node = this.getNode(nodeId);
      let parentNodeId = node.getParentNodeId();
      while (parentNodeId) {
        const checkThisNode = this.getNode(parentNodeId);
        if (checkThisNode) {
          nodePath.unshift(parentNodeId);
          parentNodeId = checkThisNode.getParentNodeId();
        }
      }
      nodePath.unshift("root");
      return nodePath;
    },

    getConnectedLinks: function(nodeId) {
      let connectedLinks = [];
      const links = Object.values(this.__links);
      for (const link of links) {
        if (link.getInputNodeId() === nodeId) {
          connectedLinks.push(link.getLinkId());
        }
        if (link.getOutputNodeId() === nodeId) {
          connectedLinks.push(link.getLinkId());
        }
      }
      return connectedLinks;
    },

    getLink: function(linkId, node1Id, node2Id) {
      const exists = Object.prototype.hasOwnProperty.call(this.__links, linkId);
      if (exists) {
        return this.__links[linkId];
      }
      const links = Object.values(this.__links);
      for (const link of links) {
        if (link.getInputNodeId() === node1Id &&
          link.getOutputNodeId() === node2Id) {
          return link;
        }
      }
      return null;
    },

    createLink: function(linkId, node1Id, node2Id) {
      let existingLink = this.getLink(linkId, node1Id, node2Id);
      if (existingLink) {
        return existingLink;
      }
      let link = new qxapp.data.model.Link(linkId, node1Id, node2Id);
      return link;
    },

    addLink: function(link) {
      const linkId = link.getLinkId();
      const node1Id = link.getInputNodeId();
      const node2Id = link.getOutputNodeId();
      let exists = this.getLink(linkId, node1Id, node2Id);
      if (!exists) {
        this.__links[linkId] = link;
      }
    },

    createNode: function(key, version, uuid, nodeData, parent) {
      let existingNode = this.getNode(uuid);
      if (existingNode) {
        return existingNode;
      }
      let node = new qxapp.data.model.Node(this, key, version, uuid);
      node.addListener("showInLogger", e => {
        this.fireDataEvent("showInLogger", e.getData());
      }, this);
      node.addListener("updatePipeline", e => {
        this.fireDataEvent("updatePipeline", e.getData());
      }, this);
      if (nodeData) {
        node.populateNodeData(nodeData);
      }
      this.addNode(node, parent);

      if (node.getMetaData() && Object.prototype.hasOwnProperty.call(node.getMetaData(), "innerNodes")) {
        const nodeMetaDatas = Object.values(node.getMetaData()["innerNodes"]);
        for (const nodeMetaData of nodeMetaDatas) {
          let innerNode = this.createNode(nodeMetaData.key, nodeMetaData.version, null, null, node);
          innerNode.populateNodeData();
        }
      }

      return node;
    },

    cloneNode: function(nodeToClone) {
      const key = nodeToClone.getKey();
      const version = nodeToClone.getVersion();
      const uuid = null;
      let node = this.createNode(key, version, uuid, nodeToClone);
      return node;
    },

    __createNodes: function(workbenchData) {
      let keys = Object.keys(workbenchData);
      // Create first all the nodes
      for (let i=0; i<keys.length; i++) {
        const nodeId = keys[i];
        const nodeData = workbenchData[nodeId];
        if (nodeData.parent && nodeData.parent !== null) {
          let parentNode = this.getNode(nodeData.parent);
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
        let parentNode = null;
        if (nodeData.parent) {
          parentNode = this.getNode(nodeData.parent);
        }
        if (nodeData.key) {
          // not container
          this.createNode(nodeData.key, nodeData.version, nodeId, null, parentNode);
        } else {
          // container
          this.createNode(null, null, nodeId, nodeData, parentNode);
        }
      }

      // Then populate them (this will avoid issues of connecting nodes that might not be created yet)
      for (let i=0; i<keys.length; i++) {
        const nodeId = keys[i];
        const nodeData = workbenchData[nodeId];
        this.getNode(nodeId).populateNodeData(nodeData);
      }
    },

    addNode: function(node, parentNode) {
      const uuid = node.getNodeId();
      if (parentNode) {
        parentNode.addInnerNode(uuid, node);
      } else {
        this.__nodesTopLevel[uuid] = node;
      }
      this.fireEvent("workbenchChanged");
    },

    removeNode: function(nodeId) {
      let node = this.getNode(nodeId);
      if (node) {
        const isTopLevel = Object.prototype.hasOwnProperty.call(this.__nodesTopLevel, nodeId);
        if (isTopLevel) {
          delete this.__nodesTopLevel[nodeId];
        }
        const parentNodeId = node.getParentNodeId();
        if (parentNodeId) {
          let parentNode = this.getNode(parentNodeId);
          parentNode.removeInnerNode(nodeId);
        }
        node.removeNode();
        this.fireEvent("workbenchChanged");
        return true;
      }
      return false;
    },

    __createLink: function(outputNodeId, inputNodeId) {
      let node = this.getNode(inputNodeId);
      if (node) {
        node.addInputNode(outputNodeId);
      }
    },

    __createLinks: function(workbenchData) {
      for (const nodeId in workbenchData) {
        const nodeData = workbenchData[nodeId];
        if (nodeData.inputNodes) {
          for (let i=0; i < nodeData.inputNodes.length; i++) {
            const outputNodeId = nodeData.inputNodes[i];
            this.__createLink(outputNodeId, nodeId);
          }
        }
      }
    },

    removeLink: function(linkId) {
      let link = this.getLink(linkId);
      if (link) {
        const inputNodeId = link.getInputNodeId();
        const outputNodeId = link.getOutputNodeId();
        let node = this.getNode(outputNodeId);
        if (node) {
          node.removeInputNode(inputNodeId);
          delete this.__links[linkId];
          return true;
        }
      }
      return false;
    },

    clearProgressData: function() {
      const allModels = this.getNodes(true);
      const nodes = Object.values(allModels);
      for (const node of nodes) {
        node.setProgress(0);
      }
    },

    serializeWorkbench: function(saveContainers = true, savePosition = true) {
      let workbench = {};
      const allModels = this.getNodes(true);
      const nodes = Object.values(allModels);
      for (const node of nodes) {
        if (!saveContainers && node.isContainer()) {
          continue;
        }

        // node generic
        let nodeEntry = workbench[node.getNodeId()] = {
          label: node.getLabel(),
          inputs: node.getInputValues(), // can a container have inputs?
          inputNodes: node.getInputNodes(),
          outputNode: node.getIsOutputNode(),
          outputs: node.getOutputValues(), // can a container have outputs?
          parent: node.getParentNodeId(),
          progress: node.getProgress()
        };

        if (savePosition) {
          nodeEntry.position = {
            x: node.getPosition().x,
            y: node.getPosition().y
          };
        }

        // node especific
        if (!node.isContainer()) {
          nodeEntry.key = node.getKey();
          nodeEntry.version = node.getVersion();
        }
      }
      return workbench;
    }
  }
});
