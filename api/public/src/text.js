function displayText(data, highlight1 = undefined, highlight2 = undefined,
                     highlight_text1 = undefined, highlight_text2 = undefined) {
  // clear the element
  document.getElementById("text")["innerText"] = "";

  // Text splicing and highlighting. Essentially parse the text correctly so that the mentioned
  // entity is colored and the sentences where they appear are also highlighted.
  let text = data.text
  // If two highlights were provided: Highlight both
  if (highlight1 !== undefined && highlight2 !== undefined) {
    // Choose order of highlights depending on indices, since it must be sorted for later
    let firstHighlight = ((highlight1[0] <= highlight2[0]) ? highlight1 : highlight2);
    let secondHighlight = ((highlight1[0] <= highlight2[0]) ? highlight2 : highlight1);

    // Could technically be overlapping, in this case we make one big annotation
    let overlapping = firstHighlight[1] > secondHighlight[0] && firstHighlight[1] <= secondHighlight[1];

    if (overlapping === true) {
      // Slicing of overlapping parts
      let firstPart = text.slice(0, firstHighlight[0]);
      let highlightedPart = text.slice(firstHighlight[0], secondHighlight[1]);
      let restPart = text.slice(secondHighlight[1], text.length);

      // highlight the actual content if found
      const highlight_regex1 = new RegExp(highlight_text1, "ig");
      const highlight_regex2 = new RegExp(highlight_text2, "ig");
      highlightedPart = highlightedPart.replace(highlight_regex1, "<span class='highlight'>$&</span>");
      highlightedPart = highlightedPart.replace(highlight_regex2, "<span class='highlight'>$&</span>");

      // Insert into text container
      let $newTextElem = $("#text");
      $newTextElem.append(firstPart);
      $newTextElem.append("<a id='anchor'>" + highlightedPart + "</a>");
      $newTextElem.append(restPart);
    } else {
      // Proper slicing of two non-overlapping parts
      let startPart = text.slice(0, firstHighlight[0]);
      let firstHighlightPart = text.slice(firstHighlight[0], firstHighlight[1]);
      let inbetweenPart = text.slice(firstHighlight[1], secondHighlight[0]);
      let secondHighlightPart = text.slice(secondHighlight[0], secondHighlight[1]);
      let endPart = text.slice(secondHighlight[1], text.length);

      // highlight the actual content if found
      const highlight_regex1 = new RegExp(highlight_text1, "ig");
      const highlight_regex2 = new RegExp(highlight_text2, "ig");
      firstHighlightPart = firstHighlightPart.replace(highlight_regex1, "<span class='highlight'>$&</span>");
      firstHighlightPart = firstHighlightPart.replace(highlight_regex2, "<span class='highlight'>$&</span>");
      secondHighlightPart = secondHighlightPart.replace(highlight_regex1, "<span class='highlight'>$&</span>");
      secondHighlightPart = secondHighlightPart.replace(highlight_regex2, "<span class='highlight'>$&</span>");

      // Insert into text container
      let $newTextElem = $("#text");
      $newTextElem.append(startPart);
      $newTextElem.append("<a id='anchor'>" + firstHighlightPart + "</a>");
      $newTextElem.append(inbetweenPart);
      $newTextElem.append("<a id='anchor2'>" + secondHighlightPart + "</a>");
      $newTextElem.append(endPart);
    }
  // only a single highlight is provided: Only highlight the first one
  } else if (highlight1 !== undefined) {
    let firstPart = text.slice(0, highlight1[0]);
    let highlightedPart = text.slice(highlight1[0], highlight1[1]);
    let restPart = text.slice(highlight1[1], text.length);

    const highlight_regex1 = new RegExp(highlight_text1, "ig");
    highlightedPart = highlightedPart.replace(highlight_regex1, "<span class='highlight'>$&</span>");

    // Insert into text container
    let $newTextElem = $("#text");
    $newTextElem.append(firstPart);
    $newTextElem.append("<a id='anchor'>" + highlightedPart + "</a>");
    $newTextElem.append(restPart);
  // No highlight is provided: Do nothing
  } else {
    $("#text").append(text);
  }

  // Scroll to anchored position
  // See https://stackoverflow.com/questions/2905867/how-to-scroll-to-specific-item-using-jquery/2906009#2906009
  let $container = $("#text-wrapper");
  let $scrollTo = $("#anchor");
  if ($scrollTo.length) {
    $container.animate({
      scrollTop: $scrollTo.offset().top - $container.offset().top + $container.scrollTop() - 20
    });
  }
}

function updateArticleOptions(doc_id) {
  return function (data) {
    document.getElementById("articles").insertAdjacentHTML("beforeend",
        "<option value='" + doc_id + "'>" + data + "</option>");

    // This variable checks if all callbacks are finished
    --num_docs_before_selector_sort;

    // Last callback
    if (num_docs_before_selector_sort <= 0) {
      let sel = $('#articles');
      let opts_list = sel.find('option');
      opts_list.sort(function(a, b) { return $(a).text() > $(b).text() ? 1 : -1; });
      sel.html('').append(opts_list);
      sel.val(opts_list[0].value);
      let firstEntry = parseInt(opts_list[0].value);
      updateText(firstEntry, 0);

      // ... and then also set the individual cooccurrences of the selected document.
      overwriteOccurrences(parseInt(firstEntry));

    }
  }
}

// This variable checks if the all callbacks are finished for overwrite articles
let num_docs_before_selector_sort = 0;


function overwriteArticles(context) {
  document.getElementById("articles").innerHTML = "";
  // This variable checks if the all callbacks are finished
  num_docs_before_selector_sort = context.size;

  for (let doc_id of context.keys()) {
    jQuery.getJSON("/text_title/" + doc_id, updateArticleOptions(doc_id));
  }

}


function overwriteOccurrences(entryID) {
  document.getElementById("occurrences").innerHTML = "";
  for (let i = 0; i < curr_context.get(entryID).length; i++) {
    document.getElementById("occurrences").insertAdjacentHTML("beforeend",
      "<option value='" + i + "'>Occurrence " + i + "</option>");
  }
  $("#occurrences").val(0);
}


function updateText(articleID, occID) {
  let newOcc = curr_context.get(articleID)[occID];
  jQuery.getJSON("/text/" + newOcc.doc_id, function (res) {
    displayText(res, newOcc.sentence1, newOcc.sentence2, newOcc.from_label, newOcc.to_label);
  });
  // Set source URL
  jQuery.getJSON("/text_link/" + newOcc.doc_id, function (res) {
    $("#source").attr("href", res);
  });
}


// On changed article, get new Occurrences
$("#articles").on("change", function() {
  // has to be int value to work on the context
  let newArticleID = parseInt(this.value);
  overwriteOccurrences(newArticleID);
  updateText(newArticleID, 0);
});


// On changed occurrence, update the text
$("#occurrences").on("change", function() {
  // has to be int value to work on the context
  let newArticleID = parseInt($("#articles").val());
  let newOccID = parseInt(this.value);
  updateText(newArticleID, newOccID);
});