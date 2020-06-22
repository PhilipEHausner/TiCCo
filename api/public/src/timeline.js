// Configuration settings
let global_timeline;
let global_timeline_items;
let global_all_timeline_items;
let old_delta = 0;
let old_start_month = 0;
let old_start_year = 0;
let old_end_month = 0;
let old_end_year = 0;


function displayTimeline(data) {
  // DOM element where the Timeline will be attached
  let container = document.getElementById('timeline');

  // global_items are the currently visible elements, global_all_items contains all items
  global_timeline_items = new vis.DataSet(data);
  global_all_timeline_items = global_timeline_items;

  // Configuration for the Timeline
  let options = {
    showCurrentTime: false,
    width: '100%',
    height: '100%',
    margin: {
      item: {
        horizontal: 0,
        vertical: 10,
      }
    },
    start: "1861-01-01",
    end: "1862-12-30",
    zoomMin: 1000 * 60 * 60 * 24 * 7,            // one week in milliseconds
    zoomMax: 1000 * 60 * 60 * 24 * 31 * 120,     // about 120 months in milliseconds
  };

  // Write nodes to different groups
  let groups = [
    {
      id: "D",
      content: "Day",
    },
    {
      id: "M",
      content: "Month",
    },
    {
      id: "Y",
      content: "Year",
    },
  ]

  // Create a Timeline
  global_timeline = new vis.Timeline(container, global_timeline_items, groups, options);

  // Highlight first rendered graph
  highlight_dates(curr_graph);

    global_timeline.on("click", function (properties) {
    // Returns all dates if no valid element is selected
    // Render new graph if only a single element was selected
    if (properties.what === "item") {
      // Retain "new current" date for increment/decrement
      let selected_time = global_all_timeline_items.get(properties.item)["title"];
      curr_graph = selected_time;
      num_nodes = default_num_nodes;

      // Rendering step
      jQuery.getJSON("/graphs/" + selected_time + "?limit=" + num_nodes, displayNetwork);

    }
  });

  // When zooming change selected granularity to avoid clutter
  global_timeline.on("rangechange", function (properties) {
    // range of displayed time in days
    let delta = (properties["end"] - properties["start"]) / (1000 * 60 * 60 * 24)

    let checkbox_year = document.getElementById("select_year_gran");
    let checkbox_month = document.getElementById("select_month_gran");
    let checkbox_day = document.getElementById("select_day_gran");

    // Change granularities that are displayed depending on zoom level
    if (delta !== old_delta) {
      // zoom out 5 years
      if (delta >= 1460 && old_delta < 1460) {
        checkbox_month.checked = false;
        checkbox_day.checked = false;
      }

      // zoom in  5 years
      if (delta < 1460 && old_delta >= 1460) {
        checkbox_month.checked = true;
      }

      // zoom out 1 year
      if (delta >= 365 && old_delta < 365) {
        checkbox_day.checked = false;
      }

      // zoom in 1 year
      if (delta < 365 && old_delta >= 365) {
        checkbox_day.checked = true;
      }
    }

    let start_month = properties.start.getMonth();
    let start_year = properties.start.getFullYear();
    let end_month = properties.end.getMonth();
    let end_year = properties.end.getFullYear();

    if ((delta !== old_delta) || (start_month !== old_start_month) || (end_month !== old_end_month)
        || (start_year !== old_start_year) || (end_year !== old_end_year)) {
      timeline_show_granularities();

      // Highlights are lost in process before. Reapply them.
      highlight_dates();
    }

    old_start_month = start_month;
    old_start_year = start_year;
    old_end_month = end_month;
    old_end_year = end_year;
    old_delta = delta;
  });
}

jQuery.getJSON("/timeline", displayTimeline);