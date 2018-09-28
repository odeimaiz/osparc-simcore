qx.Class.define("qxapp.data.Store", {
  extend: qx.core.Object,

  type : "singleton",

  events: {
    "builtInServicesRegistered": "qx.event.type.Event",
    "servicesRegistered": "qx.event.type.Event",
    "interactiveServicesRegistered": "qx.event.type.Event"
  },

  statics: {
    /**
     * Represents an empty project descriptor
    */
    NEW_PROJECT_DESCRIPTOR: qx.data.marshal.Json.createModel({
      name: "New Project",
      description: "Empty",
      thumbnail: "https://imgplaceholder.com/171x96/cccccc/757575/ion-plus-round",
      created: new Date(),
      projectId: qxapp.utils.Utils.uuidv4()
    })
  },

  members: {
    __servicesCacheBuiltIn: null,
    __servicesCacheComputational: null,
    __servicesCacheInteractive: null,

    __getMimeType: function(type) {
      let match = type.match(/^data:([^/\s]+\/[^/;\s])/);
      if (match) {
        return match[1];
      }
      return null;
    },

    __matchPortType: function(typeA, typeB) {
      if (typeA === typeB) {
        return true;
      }
      let mtA = this.__getMimeType(typeA);
      let mtB = this.__getMimeType(typeB);
      return mtA && mtB &&
        new qxapp.data.MimeType(mtA).match(new qxapp.data.MimeType(mtB));
    },

    arePortsCompatible: function(port1, port2) {
      console.log("arePortsCompatible", port1, port2);
      return this.__matchPortType(port1.portType, port2.portType) &&
        (port1.isInput !== port2.isInput);
    },

    getServices: function() {
      let services = {};
      services = Object.assign(services, this.getBuiltInServices());
      services = Object.assign(services, qxapp.dev.fake.Data.getNodeMap());
      return services;
    },

    getProjectList: function() {
      return qxapp.dev.fake.Data.getProjectList();
    },

    getProjectData: function(projectUuid) {
      return qxapp.dev.fake.Data.getProjectData(projectUuid);
    },

    getNodeMetaData: function(nodeImageId) {
      let metaData = this.getServices()[nodeImageId];
      if (metaData === undefined) {
        metaData = this.getBuiltInServices()[nodeImageId];
      }
      return metaData;
    },

    getList: function(nodeImageId) {
      switch (nodeImageId) {
        // case "service/dynamic/itis/s4l/Modeler-0.0.0": {
        case "data:application/s4l-api/modeler": {
          return [
            {
              name: "Model 1",
              uuid: "MODEL1-UUID",
              properties: {}
            }, {
              name: "Model 2",
              uuid: "MODEL2-UUID",
              properties: {}
            }, {
              name: "Model 3",
              uuid: "MODEL3-UUID",
              properties: {}
            }, {
              name: "Model 4",
              uuid: "MODEL4-UUID",
              properties: {}
            }
          ];
        }
        // case "service/dynamic/itis/s4l/MaterialDB-0.0.0": {
        case "data:application/s4l-api/materialDB": {
          return [
            {
              name: "Air",
              uuid: "Air-UUID",
              properties: {
                "massDensity": {
                  displayOrder: 0,
                  label: "Mass Density",
                  unit: "kg/m3",
                  type: "number",
                  defaultValue: 1.16409
                },
                "electricConductivity": {
                  displayOrder: 1,
                  label: "Electric Conductivity",
                  unit: "S/m",
                  type: "number",
                  defaultValue: 0
                },
                "electricRelativePermitivity": {
                  displayOrder: 2,
                  label: "Electric Relative Permeability",
                  unit: "",
                  type: "number",
                  defaultValue: 1
                },
                "magneticConductivity": {
                  displayOrder: 3,
                  label: "Magnetic Conductivity",
                  unit: "Ohm/m",
                  type: "number",
                  defaultValue: 0
                },
                "magneticRelativePermitivity": {
                  displayOrder: 4,
                  label: "Magnetic Relative Permeability",
                  unit: "",
                  type: "number",
                  defaultValue: 1
                }
              }
            }, {
              name: "Brain",
              uuid: "Brain-UUID",
              properties: {
                "massDensity": {
                  displayOrder: 0,
                  label: "Mass Density",
                  unit: "kg/m3",
                  type: "number",
                  defaultValue: 1045.5
                },
                "electricConductivity": {
                  displayOrder: 1,
                  label: "Electric Conductivity",
                  unit: "S/m",
                  type: "number",
                  defaultValue: 0.234007
                },
                "electricRelativePermitivity": {
                  displayOrder: 2,
                  label: "Electric Relative Permeability",
                  unit: "",
                  type: "number",
                  defaultValue: 1
                },
                "magneticConductivity": {
                  displayOrder: 3,
                  label: "Magnetic Conductivity",
                  unit: "Ohm/m",
                  type: "number",
                  defaultValue: 0
                },
                "magneticRelativePermitivity": {
                  displayOrder: 4,
                  label: "Magnetic Relative Permeability",
                  unit: "",
                  type: "number",
                  defaultValue: 1
                }
              }
            }, {
              name: "Eye",
              uuid: "Eye-UUID",
              properties: {
                "massDensity": {
                  displayOrder: 0,
                  label: "Mass Density",
                  unit: "kg/m3",
                  type: "number",
                  defaultValue: 1050.5
                },
                "electricConductivity": {
                  displayOrder: 1,
                  label: "Electric Conductivity",
                  unit: "S/m",
                  type: "number",
                  defaultValue: 0.62
                },
                "electricRelativePermitivity": {
                  displayOrder: 2,
                  label: "Electric Relative Permeability",
                  unit: "",
                  type: "number",
                  defaultValue: 1
                },
                "magneticConductivity": {
                  displayOrder: 3,
                  label: "Magnetic Conductivity",
                  unit: "Ohm/m",
                  type: "number",
                  defaultValue: 0
                },
                "magneticRelativePermitivity": {
                  displayOrder: 4,
                  label: "Magnetic Relative Permeability",
                  unit: "",
                  type: "number",
                  defaultValue: 1
                }
              }
            }
          ];
        }
        case "service/dynamic/itis/s4l/Simulator/LF/Materials-0.0.0": {
          return [
            {
              name: "PEC",
              uuid: "PEC-UUID",
              properties: {}
            }, {
              name: "PMC",
              uuid: "PMC-UUID",
              properties: {}
            }, {
              name: "Dielectric",
              uuid: "Dielectric-UUID",
              properties: {
                "massDensity": {
                  displayOrder: 0,
                  label: "Mass Density",
                  unit: "kg/m3",
                  type: "number",
                  defaultValue: 1000
                },
                "electricConductivity": {
                  displayOrder: 1,
                  label: "Electric Conductivity",
                  unit: "S/m",
                  type: "number",
                  defaultValue: 0
                },
                "electricRelativePermitivity": {
                  displayOrder: 2,
                  label: "Electric Relative Permeability",
                  unit: "",
                  type: "number",
                  defaultValue: 1
                },
                "magneticConductivity": {
                  displayOrder: 3,
                  label: "Magnetic Conductivity",
                  unit: "Ohm/m",
                  type: "number",
                  defaultValue: 0
                },
                "magneticRelativePermitivity": {
                  displayOrder: 4,
                  label: "Magnetic Relative Permeability",
                  unit: "",
                  type: "number",
                  defaultValue: 1
                }
              }
            }
          ];
        }
        case "service/dynamic/itis/s4l/Simulator/LF/Boundary-0.0.0": {
          return [
            {
              name: "Dirichlet",
              uuid: "Dirichlet-UUID",
              properties: {
                "constantPotential": {
                  displayOrder: 0,
                  label: "Constant Potential",
                  unit: "V",
                  type: "number",
                  defaultValue: 0
                },
                "phase": {
                  displayOrder: 1,
                  label: "Phase",
                  unit: "deg",
                  type: "number",
                  defaultValue: 0
                }
              }
            }, {
              name: "Neumann",
              uuid: "Neumann-UUID",
              properties: {
                "normalDerivative": {
                  displayOrder: 0,
                  label: "Normal Derivative",
                  unit: "V/m",
                  type: "number",
                  defaultValue: 0
                },
                "phase": {
                  displayOrder: 1,
                  label: "Phase",
                  unit: "deg",
                  type: "number",
                  defaultValue: 0
                }
              }
            }, {
              name: "Flux",
              uuid: "Flux-UUID",
              properties: {
                "constantFlux": {
                  displayOrder: 0,
                  label: "Constant Flux",
                  type: "number",
                  defaultValue: 0
                },
                "phase": {
                  displayOrder: 1,
                  label: "Phase",
                  unit: "deg",
                  type: "number",
                  defaultValue: 0
                }
              }
            }
          ];
        }
      }
      return [];
    },

    getNodeMetaDataFromCache: function(nodeImageId) {
      let metadata = this.getNodeMetaData(nodeImageId);
      if (metadata) {
        return metadata;
      }
      let services = this.__servicesCacheBuiltIn.concat(this.__servicesCacheComputational);
      services = services.concat(this.__servicesCacheInteractive);
      for (let i=0; i<services.length; i++) {
        const service = services[i];
        const id = service.key + "-" + service.version;
        if (nodeImageId === id) {
          return service;
        }
      }
      return null;
    },

    getBuiltInServices: function() {
      let builtInServices = {
        "service/dynamic/itis/FileManager-0.0.0": {
          key: "service/dynamic/itis/FileManager",
          version: "0.0.0",
          type: "dynamic",
          name: "File Manager",
          description: "File Manager",
          authors: [{
            name: "Odei Maiz",
            email: "maiz@itis.ethz.ch"
          }],
          contact: "maiz@itis.ethz.ch",
          inputs: {},
          outputs: {
            outFile: {
              displayOrder: 0,
              label: "File",
              description: "Chosen File",
              type: "data:*/*"
            },
            outDir: {
              displayOrder: 1,
              label: "Folder",
              description: "Chosen Folder",
              type: "data:*/*"
            }
          }
        },
        "service/dynamic/itis/s4l/Modeler-0.0.0": {
          key: "service/dynamic/itis/s4l/Modeler",
          version: "0.0.0",
          type: "dynamic",
          name: "Modeler",
          description: "Modeler",
          authors: [{
            name: "Odei Maiz",
            email: "maiz@itis.ethz.ch"
          }],
          contact: "maiz@itis.ethz.ch",
          inputs: {},
          outputs: {
            modeler: {
              displayOrder: 0,
              label: "Modeler",
              description: "Modeler Live link",
              type: "data:application/s4l-api/modeler"
            }
          }
        },
        "service/dynamic/itis/s4l/MaterialDB-0.0.0": {
          key: "service/dynamic/itis/s4l/MaterialDB",
          version: "0.0.0",
          type: "dynamic",
          name: "MaterialDB",
          description: "Material Database",
          authors: [{
            name: "Odei Maiz",
            email: "maiz@itis.ethz.ch"
          }],
          contact: "maiz@itis.ethz.ch",
          inputs: {},
          outputs: {
            materialDB: {
              displayOrder: 0,
              label: "MaterialDB",
              description: "MaterialDB Live link",
              type: "data:application/s4l-api/materialDB"
            }
          }
        },
        "service/container/itis/s4l/Simulator/LF-0.0.0": {
          key: "service/container/itis/s4l/Simulator/LF",
          version: "0.0.0",
          type: "container",
          name: "LF Simulator",
          description: "LF Simulator",
          authors: [{
            name: "Odei Maiz",
            email: "maiz@itis.ethz.ch"
          }],
          contact: "maiz@itis.ethz.ch",
          inputs: {
            modeler: {
              displayOrder: 0,
              label: "Modeler",
              description: "Live link to Modeler",
              type: "data:application/s4l-api/modeler"
            },
            materialDB: {
              displayOrder: 1,
              label: "MaterialDB",
              description: "Live link to Material DB",
              type: "data:application/s4l-api/materialDB"
            }
          },
          outputs: {
            outFile: {
              displayOrder: 0,
              label: "File",
              description: "LF Solver Input File",
              type: "data:application/hdf5"
            }
          },
          innerNodes: {
            "inner1": {
              key: "service/dynamic/itis/s4l/Simulator/LF/Setup",
              version: "0.0.0",
              inputNodes: [],
              outputNode: false
            },
            "inner2": {
              key: "service/dynamic/itis/s4l/Simulator/LF/Materials",
              version: "0.0.0",
              inputNodes: [
                "modeler",
                "materialDB"
              ],
              outputNode: false
            },
            "inner3": {
              key: "service/dynamic/itis/s4l/Simulator/LF/Boundary",
              version: "0.0.0",
              inputNodes: [
                "modeler"
              ],
              outputNode: false
            },
            "inner4": {
              key: "service/dynamic/itis/s4l/Simulator/LF/Sensors",
              version: "0.0.0",
              inputNodes: [
                "modeler"
              ],
              outputNode: false
            },
            "inner5": {
              key: "service/dynamic/itis/s4l/Simulator/LF/Grid",
              version: "0.0.0",
              inputNodes: [
                "modeler"
              ],
              outputNode: false
            },
            "inner6": {
              key: "service/dynamic/itis/s4l/Simulator/LF/Voxel",
              version: "0.0.0",
              inputNodes: [
                "modeler"
              ],
              outputNode: false
            },
            "inner7": {
              key: "service/dynamic/itis/s4l/Simulator/LF/SolverSettings",
              version: "0.0.0",
              inputNodes: [],
              outputNode: true
            }
          }
        },
        "service/dynamic/itis/s4l/Simulator/LF/Setup-0.0.0": {
          key: "service/dynamic/itis/s4l/Simulator/LF/Setup",
          version: "0.0.0",
          type: "computational",
          name: "LF Setup",
          description: "LF Simulator Setup Settings",
          authors: [{
            name: "Odei Maiz",
            email: "maiz@itis.ethz.ch"
          }],
          contact: "maiz@itis.ethz.ch",
          inputs: {
            frequency: {
              displayOrder: 0,
              label: "Frequency",
              description: "Frequency (Hz)",
              type: "number",
              defaultValue: 1000
            }
          },
          outputs: {
            setupSetting: {
              displayOrder: 0,
              label: "LF-Setup",
              description: "LF Setup Settings",
              type: "data:application/s4l-api/settings"
            }
          }
        },
        "service/dynamic/itis/s4l/Simulator/LF/Materials-0.0.0": {
          key: "service/dynamic/itis/s4l/Simulator/LF/Materials",
          version: "0.0.0",
          type: "dynamic",
          name: "LF Materials",
          description: "LF Simulator Material Settings",
          authors: [{
            name: "Odei Maiz",
            email: "maiz@itis.ethz.ch"
          }],
          contact: "maiz@itis.ethz.ch",
          inputs: {
            modeler: {
              displayOrder: 0,
              label: "Modeler",
              description: "Live Link to Modeler",
              type: "data:application/s4l-api/modeler"
            },
            materialDB: {
              displayOrder: 1,
              label: "MaterialDB",
              description: "Live Link to Material DB",
              type: "data:application/s4l-api/materialDB"
            },
            updateDispersive: {
              displayOrder: 2,
              label: "UpdateDispersive",
              description: "Enable automatic update of dispersive materials",
              type: "boolean",
              defaultValue: false
            }
          },
          outputs: {
            materialSetting: {
              displayOrder: 0,
              label: "MaterialSettings",
              description: "Material Settings",
              type: "data:application/s4l-api/settings"
            }
          }
        },
        "service/dynamic/itis/s4l/Simulator/LF/Boundary-0.0.0": {
          key: "service/dynamic/itis/s4l/Simulator/LF/Boundary",
          version: "0.0.0",
          type: "dynamic",
          name: "LF Boundary Conditions",
          description: "LF Simulator Boundary Conditions",
          authors: [{
            name: "Odei Maiz",
            email: "maiz@itis.ethz.ch"
          }],
          contact: "maiz@itis.ethz.ch",
          inputs: {
            modeler: {
              displayOrder: 0,
              label: "Modeler",
              description: "Live Link to Modeler",
              type: "data:application/s4l-api/modeler"
            },
            boundarySetting: {
              displayOrder: 1,
              label: "BoundarySetting",
              description: "Boundary Settings",
              type: "number",
              defaultValue: 3
            }
          },
          outputs: {
            boundarySetting: {
              displayOrder: 0,
              label: "BoundaryConditions",
              description: "Boundary Conditions",
              type: "data:application/s4l-api/settings"
            }
          }
        },
        "service/dynamic/itis/s4l/Simulator/LF/Sensors-0.0.0": {
          key: "service/dynamic/itis/s4l/Simulator/LF/Sensors",
          version: "0.0.0",
          type: "dynamic",
          name: "LF Sensors",
          description: "LF Simulator Sensors Settings",
          authors: [{
            name: "Odei Maiz",
            email: "maiz@itis.ethz.ch"
          }],
          contact: "maiz@itis.ethz.ch",
          inputs: {
            modeler: {
              displayOrder: 0,
              label: "Modeler",
              description: "Live Link to Modeler",
              type: "data:application/s4l-api/modeler"
            },
            sensorSetting: {
              displayOrder: 1,
              label: "SensorsSettings",
              description: "Sensors Settings",
              type: "number",
              defaultValue: 4
            }
          },
          outputs: {
            sensorSetting: {
              displayOrder: 0,
              label: "SensorSettings",
              description: "Sensor Settings",
              type: "data:application/s4l-api/settings"
            }
          }
        },
        "service/dynamic/itis/s4l/Simulator/LF/Grid-0.0.0": {
          key: "service/dynamic/itis/s4l/Simulator/LF/Grid",
          version: "0.0.0",
          type: "dynamic",
          name: "LF Grid",
          description: "LF Simulator Grid Settings",
          authors: [{
            name: "Odei Maiz",
            email: "maiz@itis.ethz.ch"
          }],
          contact: "maiz@itis.ethz.ch",
          inputs: {
            modeler: {
              displayOrder: 0,
              label: "Modeler",
              description: "Live Link to Modeler",
              type: "data:application/s4l-api/modeler"
            },
            materialSetting: {
              displayOrder: 1,
              label: "MaterialSettings",
              description: "Material Settings",
              type: "data:application/s4l-api/settings"
            },
            boundarySetting: {
              displayOrder: 2,
              label: "BoundarySettings",
              description: "Boundary Settings",
              type: "data:application/s4l-api/settings"
            },
            sensorSetting: {
              displayOrder: 3,
              label: "SensorSettings",
              description: "Sensor Settings",
              type: "data:application/s4l-api/settings"
            },
            gridSetting: {
              displayOrder: 4,
              label: "GridSettings",
              description: "Grid Settings",
              type: "number",
              defaultValue: 5
            }
          },
          outputs: {
            gridSetting: {
              displayOrder: 0,
              label: "GridSettings",
              description: "Grid Settings",
              type: "data:application/s4l-api/settings"
            }
          }
        },
        "service/dynamic/itis/s4l/Simulator/LF/Voxel-0.0.0": {
          key: "service/dynamic/itis/s4l/Simulator/LF/Voxel",
          version: "0.0.0",
          type: "dynamic",
          name: "LF Voxels",
          description: "LF Simulator Voxel Settings",
          authors: [{
            name: "Odei Maiz",
            email: "maiz@itis.ethz.ch"
          }],
          contact: "maiz@itis.ethz.ch",
          inputs: {
            modeler: {
              displayOrder: 0,
              label: "Modeler",
              description: "Live Link to Modeler",
              type: "data:application/s4l-api/modeler"
            },
            gridSetting: {
              displayOrder: 1,
              label: "GridSettings",
              description: "Grid Settings",
              type: "data:application/s4l-api/settings"
            },
            voxelSetting: {
              displayOrder: 2,
              label: "VoxelSettings",
              description: "Voxel Settings",
              type: "number",
              defaultValue: 6
            }
          },
          outputs: {
            voxelSetting: {
              displayOrder: 0,
              label: "VoxelSettings",
              description: "Voxel Settings",
              type: "data:application/s4l-api/settings"
            }
          }
        },
        "service/dynamic/itis/s4l/Simulator/LF/SolverSettings-0.0.0": {
          key: "service/dynamic/itis/s4l/Simulator/LF/SolverSettings",
          version: "0.0.0",
          type: "dynamic",
          name: "LF Solver Settings",
          description: "LF Simulator Solver Settings",
          authors: [{
            name: "Odei Maiz",
            email: "maiz@itis.ethz.ch"
          }],
          contact: "maiz@itis.ethz.ch",
          inputs: {
            setupSetting: {
              displayOrder: 0,
              label: "SetupSettings",
              description: "Setup Settings Out",
              type: "data:application/s4l-api/settings"
            },
            voxelSetting: {
              displayOrder: 1,
              label: "VoxelSettings",
              description: "Voxel Settings",
              type: "data:application/s4l-api/settings"
            },
            solverSetting: {
              displayOrder: 2,
              label: "SolverSetting",
              description: "Solver Setting",
              type: "number",
              defaultValue: 7
            }
          },
          outputs: {
            outFile: {
              displayOrder: 0,
              label: "Input file",
              description: "LF Solver Input File",
              type: "data:application/hdf5"
            }
          }
        },
        "service/computational/itis/Solver-LF-0.0.0": {
          key: "service/computational/itis/Solver-LF",
          version: "0.0.0",
          type: "computational",
          name: "LF Solver",
          description: "LF Solver",
          authors: [{
            name: "Odei Maiz",
            email: "maiz@itis.ethz.ch"
          }],
          contact: "maiz@itis.ethz.ch",
          inputs: {
            inFile: {
              displayOrder: 0,
              label: "Input file",
              description: "LF Solver Input File",
              type: "data:application/hdf5"
            }
          },
          outputs: {
            outFile: {
              displayOrder: 0,
              label: "Output file",
              description: "LF Solver Output File",
              type: "data:application/hdf5"
            }
          }
        }
      };
      return builtInServices;
    },

    getBuiltInServicesAsync: function() {
      let builtInServices = [];
      let builtInServicesMap = this.getBuiltInServices();
      for (const mapKey of Object.keys(builtInServicesMap)) {
        builtInServices.push(builtInServicesMap[mapKey]);
      }

      console.log("builtInServicesRegistered", builtInServices);
      let services = [];
      for (const key of Object.keys(builtInServices)) {
        const repoData = builtInServices[key];
        let newMetaData = qxapp.data.Converters.registryToMetaData(repoData);
        services.push(newMetaData);
      }
      // this.fireDataEvent("builtInServicesRegistered", builtInServices);
      this.__servicesCacheBuiltIn = services;
      this.fireDataEvent("builtInServicesRegistered", services);
    },

    getComputationalServices: function() {
      let req = new qx.io.request.Xhr();
      req.set({
        url: "/get_computational_services",
        method: "GET"
      });
      req.addListener("success", function(e) {
        let requ = e.getTarget();
        const {
          data,
          status
        } = requ.getResponse();
        if (status >= 200 && status <= 299) {
          const listOfRepositories = data;
          console.log("listOfServices", listOfRepositories);
          let services = [];
          for (const key of Object.keys(listOfRepositories)) {
            const repoData = listOfRepositories[key];
            let newMetaData = qxapp.data.Converters.registryToMetaData(repoData);
            services.push(newMetaData);
          }
          this.__servicesCacheComputational = services;
          this.fireDataEvent("servicesRegistered", services);
        } else {
          // error
          console.error("Error retrieving services: ", data);
        }
      }, this);
      req.send();
    },

    getInteractiveServices: function() {
      let socket = qxapp.wrappers.WebSocket.getInstance();
      socket.removeSlot("getInteractiveServices");
      socket.on("getInteractiveServices", function(e) {
        const {
          data,
          status
        } = e;
        if (status >= 200 && status <= 299) {
          let listOfInteractiveServices = data;
          console.log("listOfInteractiveServices", listOfInteractiveServices);
          let services = [];
          for (const key of Object.keys(listOfInteractiveServices)) {
            const repoData = listOfInteractiveServices[key];
            let newMetaData = qxapp.data.Converters.registryToMetaData(repoData);
            services.push(newMetaData);
          }
          this.__servicesCacheInteractive = services;
          this.fireDataEvent("interactiveServicesRegistered", services);
        } else {
          // error
          console.error("Error retrieving services: ", data);
        }
      }, this);
      socket.emit("getInteractiveServices");
    }
  }
});
