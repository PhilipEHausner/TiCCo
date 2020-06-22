function queryTimeline() {
    let query_terms = document.getElementById("query-field").value.trim().split(",");
    query_terms = query_terms.map(el => el.trim());

    // ignore call if query_term is empty
    if (query_terms[0]) {
        let query = "?query_terms=" + query_terms[0];
        for (let i = 1; i < query_terms.length; ++i) {
            query = query + "&query_terms=" + query_terms[i];
        }
        jQuery.getJSON("/query/query_graph_nodes/" + query, highlight_dates);
    }
}

// Originally taken and adapted from https://www.w3schools.com/howto/howto_js_autocomplete.asp
function autocomplete(inp) {
  let currentFocus;
  // execute a function when someone writes in the text field:
  inp.addEventListener("input", function(e) {
    let a, b, i, val = this.value;
    val = val.trim().split(",");
    val = val[val.length -1].trim();
    // close any already open lists of autocompleted values
    closeAllLists();
    if (!val) { return false;}
    currentFocus = -1;
    // create a DIV element that will contain the items (values):
    a = document.createElement("DIV");
    a.setAttribute("id", "autocomplete-list");
    a.setAttribute("class", "autocomplete-items");
    // append the DIV element as a child of the autocomplete container:
    this.parentNode.appendChild(a);

    jQuery.getJSON("/query/suggest/" + val , function (arr) {
      for (i = 0; i < arr.length; i++) {
        // Create a DIV element for each matching element:
        b = document.createElement("DIV");
        // Make the matching letters bold:
        b.innerHTML = arr[i];
        // Insert a input field that will hold the current array item's value:
        b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
        // Execute a function when someone clicks on the item value (DIV element):
        b.addEventListener("click", function(e) {
          // Insert the value for the autocomplete text field:
          // Do this by inserting before the last comma.
          let prev_val = document.getElementById("query-field").value;
          if (prev_val.lastIndexOf(',') > 0) {
              prev_val = prev_val.substr(0, prev_val.lastIndexOf(', ')) + ", ";
          } else {
              prev_val = ""
          }
          inp.value = prev_val + this.getElementsByTagName("input")[0].value;
          // Close the list of autocompleted values
          queryTimeline();
          closeAllLists();
        });
        a.appendChild(b);
      }
    });
  });

  // Execute a function presses a key on the keyboard:
  inp.addEventListener("keydown", function(e) {
    let autocomplete_list = document.getElementById( "autocomplete-list");
    if (autocomplete_list) autocomplete_list = autocomplete_list.getElementsByTagName("div");
    if (e.key === "ArrowDown") { // down
      // If the arrow DOWN key is pressed, increase the currentFocus variable:
      currentFocus++;
      // and and make the current item more visible:
      addActive(autocomplete_list);
    } else if (e.key === "ArrowUp") { //up
      // If the arrow UP key is pressed, decrease the currentFocus variable:
      currentFocus--;
      addActive(autocomplete_list);
    } else if (e.key === "Enter") {
      // If Enter is pressed, autocomplete the current value
      if (currentFocus > -1) {
        if (autocomplete_list) {
          autocomplete_list[currentFocus].click();
          queryTimeline();
        }
      }
    }
  });

  function addActive(x) {
    if (!x) return false;
    // start by removing the "active" class on all items:
    removeActive(x);
    if (currentFocus >= x.length) currentFocus = 0;
    if (currentFocus < 0) currentFocus = (x.length - 1);
    // add class "autocomplete-active":
    x[currentFocus].classList.add("autocomplete-active");
  }

  function removeActive(x) {
    // remove the "active" class from all autocomplete items:
    for (var i = 0; i < x.length; i++) {
      x[i].classList.remove("autocomplete-active");
    }
  }

  function closeAllLists(elmnt) {
    // Close all autocomplete lists in the document, except the one passed as an argument:
    var x = document.getElementsByClassName("autocomplete-items");
    for (var i = 0; i < x.length; i++) {
      if (elmnt != x[i] && elmnt != inp) {
        x[i].parentNode.removeChild(x[i]);
      }
    }
  }

  // Close the autocomplete list when a click on other elements is registered
  document.addEventListener("click", function (e) {
    closeAllLists(e.target);
  });
}

autocomplete(document.getElementById("query-field"));