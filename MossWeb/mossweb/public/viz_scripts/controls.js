/**
 * Setup the default control values
 */
var graphControls = {

    // Whether not to show matches from past semesters
    includePastSemesters:false,

    // Whether or not to show nodes with no matches
    includeSingletons:false,

    // Whether or not to show edges that are partners
    includePartnerEdges:true,

    // Whether or not to include the solution node
    includeSolution:true,

    // Whether or not to make the graph anonymous
    anonymousGraph:true,

    // The minimum threshold for edges to display
    minimumEdgeWeight:0,

    // Whether or not to use the fisheye view for mouse moving
    useFisheye: false
};




/**
 * Initialize the controls sidebar, creating & binding all inputs to their corresponding actions (everything is disabled by default)
 */
function initializeControls() {
	/**
	 * Triggered when a user selects a minimum edge weight (i.e. *stops* on a certain weight)
	 */
	var changeMinimumEdgeWeight = function(event, ui) {
	    graphControls.minimumEdgeWeight = ui.value;
	    $('#updateGraphButton').attr('disabled', false);
	};
	
	/**
	 * When one of the checkboxes is toggled, set/unset the corresponding option
	 */
	var toggleIncludePastSemesters = function() {
	    graphControls.includePastSemesters = this.checked;
	    $('#updateGraphButton').attr('disabled', false);
	};
	var toggleIncludeSingletons = function() {
	    graphControls.includeSingletons = this.checked;
	    $('#updateGraphButton').attr('disabled', false);
	};
	var toggleIncludePartnerEdges = function() {
	    graphControls.includePartnerEdges = this.checked;
	    $('#updateGraphButton').attr('disabled', false);
	};
	var toggleIncludeSolution = function() {
	    graphControls.includeSolution = this.checked;
	    $('#updateGraphButton').attr('disabled', false);
	};
	var toggleAnonymousGraph = function() {
	    graphControls.anonymousGraph = this.checked;
	    $('#updateGraphButton').attr('disabled', false);
	};
	var sliderChangeFunc = function (event, ui) {
    	$("#currentMinimumEdgeWeight").text(ui.value);
    };
    var toggleUseFisheye = function() {
        graphControls.useFisheye = this.checked;
        $('#updateGraphButton').attr('disabled', false);
    };

    // Create slider & attach listener
    $("#minimumEdgeWeightSlider").slider({
        min:0,
        max:100,
        disabled:true,
        stop:changeMinimumEdgeWeight,
        slide: sliderChangeFunc,
        change: sliderChangeFunc
    });

    // Attach handlers to checkbox controls
    $("#includePastSemestersCheckbox").change(toggleIncludePastSemesters);
    $("#includeSingletonsCheckbox").change(toggleIncludeSingletons);
    $("#includePartnerEdgesCheckbox").change(toggleIncludePartnerEdges);
    $("#includeSolutionCheckbox").change(toggleIncludeSolution);
    $("#anonymousGraphCheckbox").change(toggleAnonymousGraph);
    $("#useFisheyeCheckbox").change(toggleUseFisheye);

    // Disable everything in the controls
    $('#right-sidebar *').attr('disabled', true);
}


/**
 * Enable the controls to allow them to be used
 */
function enableControls() {
    $('#right-sidebar *').attr('disabled', false);
    $("#minimumEdgeWeightSlider").slider("option", "disabled", false);
    $('#updateGraphButton').attr('disabled', true);
}

/**
 * Hide the legend
 */
function hideLegend() {
    $("#legend").hide();
}

/**
 * Draw & show the legend
 */
function showLegend() {

    // Build the legend HTMl for submission coloring
    var submissionLegendHTML = "<table cellpadding='5'>";
    for (var groupId in groupIds) {

        // Determine the label for this group
        var offeringName;
        if (groupId >= 0) {
            offeringName = offerings[groupId].semester.season + " " + offerings[groupId].semester.year;
        } else {
            offeringName = "Solution";
        }

        submissionLegendHTML += "<tr>" +
            "<td><svg height=10 width=10><circle cx='5' cy='5' style='fill: " + fillNode({group:groupId}) + "' r='5'></circle></svg></td>" +
            "<td>" + offeringName + "</td>" +
            "</tr>";
    }
    
    // Add entries for specially colored nodes based on matches
    submissionLegendHTML += "<tr>" +
        "<td><svg height=10 width=10><circle cx='5' cy='5' style='fill: "
        + fillNode({hasSolutionMatch:true, hasCrossSemesterMatch:true}) + "' r='5'></circle></svg></td>" +
        "<td>Matches Solution <i>and</i> Other Semester</td>" +
        "</tr>";
    submissionLegendHTML += "<tr>" +
        "<td><svg height=10 width=10><circle cx='5' cy='5' style='fill: "
            + fillNode({hasSolutionMatch:true, hasCrossSemesterMatch:false}) + "' r='5'></circle></svg></td>" +
        "<td>Matches Solution</td>" +
        "</tr>";
    submissionLegendHTML += "<tr>" +
        "<td><svg height=10 width=10><circle cx='5' cy='5' style='fill: "
        + fillNode({hasSolutionMatch:false, hasCrossSemesterMatch:true, offering_id:currentOfferingId}) + "' r='5'></circle></svg></td>" +
        "<td>Matches Other Semester</td>" +
        "</tr>";
    submissionLegendHTML += "</table>";

    // Build the legend HTMl for submission coloring
    var matchLegendHTML = "<table cellpadding='5'>";


    // Add partner match legend if partner edges are shown
    if (graphControls.includePartnerEdges) {
        matchLegendHTML += "<tr>" +
            "<td><svg height=10 width=10><line class='link' style=\"stroke-width: 3px; stroke-opacity: 1.0; stroke:" +
            colorMatchEdge({isSolutionMatch:false, isPartnerMatch:true, isCrossSemesterMatch:false}) +
            ";\" x1='1' x2='10' y1='5' y2='5'></line></svg></td>" +
            "<td>Partner Matches</td>" +
            "</tr>";
    }

    // Add solution match legend if partner edges are shown
    if (graphControls.includeSolution) {
        matchLegendHTML += "<tr>" +
            "<td><svg height=10 width=10><line class='link' style=\"stroke-width: 3px; stroke-opacity: 1.0; stroke:" +
            colorMatchEdge({isSolutionMatch:true, isPartnerMatch:false, isCrossSemesterMatch:false}) +
            ";\" x1='1' x2='10' y1='5' y2='5'></line></svg></td>" +
            "<td>Solution Matches</td>" +
            "</tr>";
    }

    // Add partner match legend if partner edges are shown
    if (graphControls.includePastSemesters) {
        matchLegendHTML += "<tr>" +
            "<td><svg height=10 width=10><line class='link' style=\"stroke-width: 3px; stroke-opacity: 1.0; stroke:" +
            colorMatchEdge({isSolutionMatch:false, isPartnerMatch:false, isCrossSemesterMatch:true}) +
            ";\" x1='1' x2='10' y1='5' y2='5'></line></svg></td>" +
            "<td>Cross-Semester Matches</td>" +
            "</tr>";
    }

    // Show the legend (set the HTML & smoothly fade it in
    $("#legend .post").html(submissionLegendHTML + matchLegendHTML);
    $("#legend").fadeIn('fast');
}


/**
 * Exports the current graph as an SVG for the user
 */
var exportImage = function(){
	var serializer = new XMLSerializer();
	var svg = serializer.serializeToString($("svg")[0]);
	$("#exportSVG").val(svg);
	$("#exportForm").submit();
};
