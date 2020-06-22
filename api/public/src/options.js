let last_dates = [];

function highlight_dates(dates = null) {
  // Function can be called with null to highlight the same dates as the time before
  if (dates === null) {
      dates = last_dates;
  }

  // Get all indices that are supposed to be highlighted (i.e. that represent one of the given dates)
  let highlight_indices= [];
  for (let idx of global_timeline_items.getIds()) {
      let item = global_timeline_items.get(idx)
      if (dates.indexOf(item["title"]) >= 0) {
          highlight_indices.push(item["id"])
      }
  }
  last_dates = dates;
  global_timeline.setSelection(highlight_indices)
}

function timeline_show_granularities() {
  // Get selections from checkboxes
  let show_year = document.getElementById("select_year_gran").checked;
  let show_month = document.getElementById("select_month_gran").checked;
  let show_day = document.getElementById("select_day_gran").checked;

  // alter visibility of groups
  let groups = [
    {
      id: "D",
      content: "Day",
      visible: show_day,
    },
    {
      id: "M",
      content: "Month",
      visible: show_month,
    },
    {
      id: "Y",
      content: "Year",
      visible: show_year,
    },
  ];

  global_timeline.setGroups(groups);
}
