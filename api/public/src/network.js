// Configuration
let increment = 2;
let num_nodes = 10;
let default_num_nodes = 10;  // Resets for a new network
let date_re = /\d{4}(-d{2}(-d{2})?)?/;  // YYYY-MM-DD format as per preprocessing
let curr_graph = "1862";  // Default graph setting
let curr_context;  // Holds entity-specific documents


// Color schema
let primaryColor = "#9ACD32";
let secondaryColor = "#668E16";
let highlightColor = "#E3B019";
let highlightBorderColor = "#3F580E";


function displayNetwork(data) {
  // DOM element where the Timeline will be attached
  let container = document.getElementById('network');

  let nodes = new vis.DataSet(data.nodes, {"fieldId": "id"});
  let edges = new vis.DataSet(data.edges, {"fieldId": "id"});

  let options = {
    autoResize: true,
    layout: {
      randomSeed: 1312,
      improvedLayout: true,
    },
    physics: {
      barnesHut: {
        gravitationalConstant: -50,
        springLength: 50,
        springConstant: 0,
        avoidOverlap: 0.4,
      }
    },
    width: '100%',
    nodes: {
      borderWidth: 2,
      shape: 'box',
      scaling: {
        label: {
          min: 20,
          max: 20
        },
      },
      font: {
        face: 'Roboto Slab',
      },
      color: {
        border: secondaryColor,
        background: primaryColor,
        highlight: {
          border: highlightBorderColor,
          background: primaryColor,
        },
        hover: {
          border: secondaryColor,
          background: primaryColor,
        },
      },
      shadow: {
        enabled: true,
        size: 6,
      }
    },
    edges: {
      color: {
        color: secondaryColor,
        opacity: 0.85,
        hover: primaryColor,
        highlight: highlightColor,
      },
      scaling: {
        min: 1,
        max: 6,
      },
      selectionWidth: 4,
      shadow: {
        enabled: false,
        size: 1,
        x: 0,
        y: 0,
      }
    },
    interaction: {
      hover: true
    },
  };

  let graph = {
    nodes: nodes,
    edges: edges
  };

  let network = new vis.Network(container, graph, options);

  // Display graph's date in header element
  $("#network-display-time").text(curr_graph);

  // And display related graph options
  displayRelatedDates(data.nodes);

  // On click display relevant text with highlight
  network.on("click", function(params) {
    // Collect all sentences that are associated
    let sents = [];
    for (let curr_edge_hash of params.edges) {
      let temp_edge = edges.get(curr_edge_hash);
      let curr_from_label = nodes.get(temp_edge.from)["label"];
      let curr_to_label = nodes.get(temp_edge.to)["label"];
      if (temp_edge.sent_functionality) {
        for (let cooc of temp_edge.sent_functionality) {
          cooc["from_label"] = curr_from_label;
          cooc["to_label"] = curr_to_label;
          sents.push(cooc);
        }
      }
    }

    // Check whether click was on node/edge
    if (sents.length > 0) {
      // group by individual documentIDs
      curr_context = groupBy(sents, sent => sent.doc_id);
      // Put all the collected elements into the dropdown menu
      overwriteArticles(curr_context);

    }
  });

  // On right click start a query containing the term of the node
  network.on("oncontext", function (params) {
    params.event.preventDefault();
    let nodeID = network.getNodeAt({x: params.pointer["DOM"]["x"], y: params.pointer["DOM"]["y"]});
    if (nodeID) {
      let curr_query = document.getElementById("query-field").value;
      // Append if previous query terms exist
      if (curr_query) {
        curr_query = curr_query + ", " + nodes.get([nodeID])[0]["label"];
      } else {
        curr_query = nodes.get([nodeID])[0]["label"];
      }
       document.getElementById("query-field").value = curr_query;
      queryTimeline();
    }
  });

  // Change/Revert mouse pointer on node hover
  network.on("hoverNode", function (params) {
    network.canvas.body.container.style.cursor = 'pointer'
   });
  network.on("blurNode", function (params) {
    network.canvas.body.container.style.cursor = 'auto'
   });
}


// Helper function from https://stackoverflow.com/a/38327540/3607203
function groupBy(list, keyGetter) {
    const map = new Map();
    list.forEach((item) => {
         const key = keyGetter(item);
         const collection = map.get(key);
         if (!collection) {
             map.set(key, [item]);
         } else {
             collection.push(item);
         }
    });
    return map;
}


function displayRelatedDates(nodes) {
  document.getElementById("opt-granular").innerHTML = "";
  // The following works because we always have Y-M-D order
  let fullGranularity = ""
  // Iterate over all different granularities, excluding the current one.
  let validLevels = curr_graph.split("-");
  // Remove last element (which is the current granularity)
  validLevels.pop();
  // Display all other granularities
  for (let granularity of validLevels) {
    fullGranularity += granularity;
    document.getElementById("opt-granular").insertAdjacentHTML("beforeend",
      "<option value='" + fullGranularity + "'>" + fullGranularity + "</option>");
    fullGranularity += "-";
  }

  // Update related dates based on nodes
  document.getElementById("opt-related").innerHTML = "";
  for (node of nodes) {
    if (node.label !== curr_graph && date_re.test(node.label)) {
      document.getElementById("opt-related").insertAdjacentHTML("beforeend",
      "<option value='" + node.label + "'>" + node.label + "</option>");
    }
  }

  // Set to default value
  $("#select-related").val("default");
}


// Click handler for more/less nodes
$("#more").click(function() {
  if (num_nodes + increment >= 25) {
    alert("Performance of graph rendering will drop significantly!")
  }
  num_nodes = num_nodes + increment;
  jQuery.getJSON("/graphs/" + curr_graph + "?limit=" + num_nodes, displayNetwork);
});

$("#less").click(function() {
  // Assert no negative number of nodes is rendered
  if (num_nodes - increment >= 0) {
    num_nodes = num_nodes - increment;
    jQuery.getJSON("/graphs/" + curr_graph + "?limit=" + num_nodes, displayNetwork);
  }
});

// on-change for related graph
$("#select-related").on("change", function() {
  let newGraphID = this.value;
  // Reset parameters and render new graph
  curr_graph = newGraphID;
  num_nodes = default_num_nodes;
  jQuery.getJSON("/graphs/" + newGraphID + "?limit=" + num_nodes, displayNetwork);
  highlight_dates([curr_graph]);
});

