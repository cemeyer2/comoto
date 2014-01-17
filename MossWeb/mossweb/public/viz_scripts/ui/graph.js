// Used to keep track of the groups that are shown in the graph
var groupIds;

//boolean true if mouse is over a node, false otherwise
var overNode = false;

// Record the mouse location at all times
var mouseX, mouseY;
$(document).ready(function () {
    $(document).mousemove(function (e) {
        mouseX = e.pageX;
        mouseY = e.pageY;
    });
});


/**
 * Toggle fade a submission node from the graph, given the submission object.
 */
function toggleFadeSubmissionNode(submission) {

    // Gather all of HTML element ids to remvoe
    var submissionElementId = "submission" + submission.id;
    var matchElementIds = [];
    for (var matchIndex in matches) {
        var match = matches[matchIndex];
        if 	( 	(match.submission_1_id === submission.id || match.submission_2_id === submission.id)
            && $("#submission"+submission.id).css('opacity') == $("#match" + matches[matchIndex].id).css('opacity') //bug here, when the 2 nodes are both dimmed, itll still add the edge when it shouldnt
            ){
            matchElementIds.push("match" + matches[matchIndex].id);
        }
    }

    var fade = function(node){
        var low = .2;
        var high = 1;
        var speed = 'fast';
        var current = Math.round(parseFloat(node.css('opacity')));
        if(current == 0){
            node.fadeTo(speed, high);
        } else {
            node.fadeTo(speed, low);
        }
    };

    // Fade this submission and all associated matches
    fade($("#" + submissionElementId));
    for (var matchIdIndex in matchElementIds) {
        var matchId = matchElementIds[matchIdIndex];
        fade($("#" + matchId));
    }
}


/**
 * Build the match links for the graph
 * @param vis   The root d3.js visualization object
 * @param data  The data to render in the graph
 */
function buildMatchLinks(vis, data) {

    // Configure links (edges)
    var links = vis.selectAll("line.link")
        .data(data.links)
        .enter();

    // Attach elements & attributes
    links = links.append("line")
        .attr("stroke", "#999")
        .style("stroke-opacity", ".6")
        .style("stroke-width", function (match) {

            // Configure it between 0 and 10 px wide
            var value = match.value / 100.0;
            return 3 + (value * value) * 5;
        })
        .attr("x1", function (match) {
            return match.source.x;
        })
        .attr("y1", function (match) {
            return match.source.y;
        })
        .attr("x2", function (match) {
            return match.target.x;
        })
        .attr("y2", function (match) {
            return match.target.y;
        })
        .attr("id", function (match) {
            return "match" + match.id;
        })
        .style("stroke", colorMatchEdge);

    // Attach mouseover functionality
    links.each(function(match) {

            // Initialize the popover for this match
            match.lockedPopover = false;
            $('#match' + match.id).popover({
                delay: graphControls.useFisheye ? 0 : 500,
                animation: !graphControls.useFisheye,
                placement: function(popover) {

                    // Just attach an id to the popover
                    popover.id = 'matchPopover' + match.id;
                    return 'right';
                },
                trigger: 'manual',
                title: generateMatchPopoverTitle(match),
                content: generateMatchPopoverContent(match)
            });
        })
        .on("mouseover", function (match) {
            if(!match.lockedPopover) {

                $('#match' + match.id).popover('show');

                // Calculate the position & move the popover
                var matchPopover = $('#matchPopover' + match.id);
                matchPopover.offset({
                    left: mouseX + 5,
                    top: mouseY - matchPopover.height()/2
                });
            }
        })
        .on("mouseout", function (match) {
            if(!match.lockedPopover) {
                $('#match' + match.id).popover('hide');
            }
        })
        .on("click", function(match) {
            match.lockedPopover = !match.lockedPopover;
        });

    return links;
}


/**
 * Builds the submission nodes of the graph
 * @param vis   The visualization itself (root d3.js object)
 * @param data  The data to attach to the graph
 * @param force The force-directed layout from d3
 */
function buildSubmissionNodes(vis, data, force) {

    // Layout the nodes using the force directed graph
    var nodes = vis.selectAll("circle.node")
        .data(data.nodes)
        .enter();

    // Add the node elements & attributes
    nodes = nodes.append("circle")
        .attr("stroke", "#fff")
        .style("stroke-width", "1.5px")
        .attr("cx", function (d) {
            return d.x;
        })
        .attr("cy", function (d) {
            return d.y;
        })
        .attr("r", 5)
        .attr("id", function (d) {
            return "submission" + d.id;
        })
        .style("fill", function (submission) {
            groupIds[submission.group] = true;
            return fillNode(submission);
        });

    // Attach drag listener to nodes only if not using fisheye
    if(!graphControls.useFisheye) {
        nodes.call(force.drag);
    }

    // Initialize the mouseover functionality
    nodes.each(function(submission) {

            // Initialize the popover for this submission
            submission.lockedPopover = false;
            $('#submission' + submission.id).popover({
                delay: graphControls.useFisheye ? 0 : 500,
                animation: !graphControls.useFisheye,
                placement: function(popover) {

                    // Just attach an id to the popover
                    popover.id = 'submissionPopover' + submission.id;
                    return 'right';
                },
                trigger: 'manual',
                title: generateSubmissionPopoverTitle(submission),
                content: generateSubmissionPopoverContent(submission)
            });
        })
        .on("mouseover", function (submission) {

            // Mark that this node is being hovered, and show the popover
            overNode = true;
            if (!submission.lockedPopover) {

                var submissionNode = $('#submission' + submission.id);
                submissionNode.popover('show');
                var r = parseFloat(submissionNode.attr('r'));

                // Find & position the popover
                var submissionPopover = $('#submissionPopover' + submission.id);
                submissionPopover.offset({
                   left: mouseX + r,
                   top: mouseY - submissionPopover.height()/2
                });
            }
        })
        .on("mouseout", function (submission) {

            // Mark that this node is no longer being hovered, and hide the popover if not locked in place
            overNode = false;
            if(!submission.lockedPopover) {
                $('#submission' + submission.id).popover('hide');
            }
        })
        .on("click", function(submission) {
            submission.lockedPopover = !submission.lockedPopover;
        })
        .on("contextmenu", toggleFadeSubmissionNode);

    return nodes;
}


/**
 * Render the graph given the graph data structure
 */
function renderGraph(data) {

     // Remove all entries in the submission list
    $('#submissionList').children().remove();
    $('#submissionList, #submissionListTitle').hide();

    // Hide all popups on the graph
    hideLegend();
    $('.popover').hide();

    // Resize the content div
    var width = $("#page").width() - 490; // Subtract 400 pixels for left/right sidebars
    var height = $("#page").height() - 10; // Subtract 10 pixels for top/bottom content border of 5 px

    // Resize content
    $("#content").height(height);
    $("#content").width(width);

    // Attach drag handlers
    var redraw = function () {
    	if(!overNode){
            $('.popover').hide(); // Hide popovers while dragging
	        vis.attr("transform",
	            "translate(" + d3.event.translate + ")"
	                + " scale(" + d3.event.scale + ")");
        }
    };

    groupIds = {};

    // Create the graph element
    var vis = d3.select("#chart").append("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("pointer-events", "all")
        .append('svg:g')
        .call(d3.behavior.zoom().on("zoom", redraw))
        .append('svg:g');

    // Add the background rectangle to allow panning
    var graphBackground = vis.append('svg:rect')
        .attr('width', width*5)
        .attr('height', height*5)
        .attr('x', (-2) * width)
        .attr('y', (-2) * height)
        .attr('fill', 'white');

    // Attach listeners to hide other popups on mouseover a popup
    $("#nodePopup").hover(function () {
        $("#edgePopup").hide();
    });
    $("#edgePopup").hover(function () {
        $("#nodePopup").hide();
    });

    // Create the graph
    var force = d3.layout.force()
        .charge(-120)
	    .linkDistance(60)
        .nodes(data.nodes)
        .links(data.links)
        .size([width, height])
        .start();



    // Add the text labels to submission nodes
    var text = vis.selectAll("text")
        .data(data.nodes)
        .enter()
        .append("svg:text")
        .attr("class", "nodetext")
        .attr("dx", 12)
        .attr("dy", 3)
        .text(function (submission) {

            // Check if the submission should be displayed, and display the correct text if it is (otherwise no text)
            if (submission.type == 'solutionsubmission') {
                return "Solution";
            } else if (graphControls.anonymousGraph) {
                return submission.id;
            } else {
                return submission.student.netid
            }
        });
        
            // Build the match links for the graph
    var links = buildMatchLinks(vis, data);

    // Build the submssion nodes of the graph
    var nodes = buildSubmissionNodes(vis, data, force);

    // Update the location of the nodes, doing a 'tick' of the force directed layout algorithm
    force.on("tick", function () {
        links.attr("x1", function (d) {
            return d.source.x;
        })
        .attr("y1", function (d) {
            return d.source.y;
        })
        .attr("x2", function (d) {
            return d.target.x;
        })
        .attr("y2", function (d) {
            return d.target.y;
        });

        nodes.attr("cx", function (d) {
            return d.x;
        }).attr("cy", function (d) {
            return d.y;
        });

        // Set the location of the node labels
        vis.selectAll(".nodetext")
            .attr("transform", function (d) {
                return "translate(" + d.x + "," + d.y + ")";
            });
    });


    // Helper function to attach fisheye functionality
    var attachFisheye = function() {

        var fisheye = d3.fisheye()
            .radius(200)
            .power(2);

        // Apply the fisheye effect on mousemove
        graphBackground.on('mousemove', function() {

            // Draw fisheye effect on mouse moving
            fisheye.center(d3.mouse(this));

            nodes
                .each(function(d) { d.display = fisheye(d); })
                .attr("cx", function(d) { return d.display.x; })
                .attr("cy", function(d) { return d.display.y; })
                .attr("r", function(d) { return d.display.z * 4.5; });

            links
                .attr("x1", function(d) { return d.source.display.x; })
                .attr("y1", function(d) { return d.source.display.y; })
                .attr("x2", function(d) { return d.target.display.x; })
                .attr("y2", function(d) { return d.target.display.y; });

            // Set the location of the node labels
            vis.selectAll(".nodetext")
                .attr("transform", function (d) {
                    return "translate(" + d.display.x + "," + d.display.y + ")";
                });
        });
    };

    // Just stop the force directed computation after 10 seconds, THEN attach fisheye functionality if we're supposed to
    setTimeout(function() {
        force.stop();
        if(graphControls.useFisheye) {
            attachFisheye();
        }
    }, 8000);

    // Show the legend
    showLegend();

    // Re-add all submissions that were previously on the submission list to the list
    for(var i in submissionIdsOnList) {
        if(submissionIdsOnList.hasOwnProperty(i)) {
            addSubmissionToList(submissionIdsOnList[i]);
        }
    }
}


/**
 * Remove a submission from the sidebar list
 */
function removeSubmissionFromList(submissionId) {
    $('#submissionEntry' + submissionId).remove();
    var index = submissionIdsOnList.indexOf(submissionId);
    submissionIdsOnList.splice(index,  1);
    if(submissionIdsOnList.length === 0) {
        $('#submissionList').children().remove();
        $('#submissionList, #submissionListTitle').hide();
    }
}


/**
 * Add a submission to the submission list
 *  @param submissionId The id of the submission to add to the submission list
 */
function addSubmissionToList(submissionId) {

    // Get the submission from the list of submissions
    var submission = submissions[submissionId];
    var submissionListEntryHTML = "";

    // Generate the HTML for the submission list entry (add close/remove button)
    submissionListEntryHTML += "<ul class='treeview' id='submissionEntry" + submissionId + "'> Submission " + submissionId +
        "<div class='closeButton close' onclick='javascript:removeSubmissionFromList(" + submissionId + ");'>X</div>";

    // Add HTML for matches
    submissionListEntryHTML += "<li>Matches<ul>";
    for (var matchIndex in matches) {
        var match = matches[matchIndex];
        var averageScore = (match.score1 + match.score2) / 2.0;
        submissionListEntryHTML += "<li>Match " + match.id + "<ul>";
        submissionListEntryHTML += "<li>Strength: " + averageScore + "</li>";
        submissionListEntryHTML += "<li><a href='" + match.link + "'>Analysis</a></li>";
        submissionListEntryHTML += "</ul></li>";
    }
    submissionListEntryHTML += "</ul>";

    // Add HTML for student data
    var student = submission.student;
    submissionListEntryHTML += "<li>Student<ul>";
    if (graphControls.anonymousGraph) {
        submissionListEntryHTML += "<li>Id " + student.id + "</li>";
        submissionListEntryHTML += "<li><a href='" + student.history_link + "'>Student History</a></li>";
    } else {
        submissionListEntryHTML += "<li>" + student.display_name + "</li>";
        submissionListEntryHTML += "<li>" + student.netid + "</li>";
        submissionListEntryHTML += "<li>" + student.program_name + "</li>";
        submissionListEntryHTML += "<li>" + student.level_name + "</li>";
        submissionListEntryHTML += "<li><a href='" + student.history_link + "'>Student History</a></li>";
    }
    submissionListEntryHTML += "</ul></li>";
    submissionListEntryHTML += "</ul>";

    // Add the generated HTML to the submission list
    $("#submissionListTitle").show();
    $("#submissionList").append("<li>" + submissionListEntryHTML + "</li>");
    $("#submissionList").show();

    // Turn this entry into a treeview structure
    $("#submissionEntry" + submissionId).treeview({
        animated:"fast",
        collapsed:true,
        unique:true
    });
}