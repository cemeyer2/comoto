/**
 * Helper function to add a submission to the list
 */
function addSubmissionNodeToList(submissionId) {

    // Add the submission to the list
    addSubmissionToList(submissionId);

    // Add the submission id to the list of submission ids on the list
    if(submissionIdsOnList.indexOf(submissionId) < 0) {
        submissionIdsOnList.push(submissionId);
    }
}


/**
 * Generate the popover title bar HTML for a submission
 */
function generateSubmissionPopoverTitle(submission) {

    if (submission.type === 'solutionsubmission') {
        return null;
    } else {

        var addButton = "<button class='addButton close' title='Add to List' onclick=addSubmissionNodeToList("
            + submission.id + ")>+</button>";

        if (graphControls.anonymousGraph) {
            return "<p><span class='header'>Student Id:</span>" + submission.student.id + addButton + "</p>";
        } else {
            return "<p><span class='header'>Name:</span>" + submission.student.display_name + addButton + "</p>";
        }
    }
}


/**
 * Generate the popover content for a submission
 */
function generateSubmissionPopoverContent(submission) {

    if (submission.type === 'solutionsubmission') {

        // Create the HTML for the node popover that just says it's the solution
        return "<h3 style='color:#CC0001;'>&nbsp;&nbsp;Solution Submission&nbsp;&nbsp;</h3>";

    } else {

        // Nicely format the student's academic status
        var studentStatus;
        var studentProgram;
        if (submission.student.left_uiuc === "currently enrolled") {
            studentStatus = submission.student.level_name + " (" + submission.student.left_uiuc + ")";
            studentProgram = submission.student.program_name
        } else {
            studentStatus = "Left UIUC " + submission.student.left_uiuc;
            studentProgram = "N/A";
        }

        // Generate the HTML for the urls of cross-semester matches
        var matchLinksHTML = "";
        for (var edgeIndex in submission.crossSemesterMatches) {
            if(submission.crossSemesterMatches.hasOwnProperty(edgeIndex)) {
                var match = submission.crossSemesterMatches[edgeIndex];

                // Show the match in the list only if it satisfies the weight edge predicate
                var minimumEdgeWeightPredicate = graphControls.minimumEdgeWeight <= (match['score1'] + match['score1']) / 2;
                if(minimumEdgeWeightPredicate) {
                    matchLinksHTML += "<a href='" + match.link + "' target='_blank'>View Moss Match Details</a><br/>";
                }
            }
        }
        if(matchLinksHTML === "") {
            matchLinksHTML = "None";
        } else {
            matchLinksHTML = matchLinksHTML.slice(0,matchLinksHTML.length-5); // Remove the last line break
        }

        // Return the html content of the popup (vary based on graph anonymity controls)
        if (graphControls.anonymousGraph) {
            return "<p>" +
                "<span class='header'>History Link:</span><br/>" +
                "<a class='post' target='_newtab' href='" + submission.student.history_link + "'>View Student History</a>" +
                "</p><p>" +
                "<span class='header'>Cross Semester Matches:</span><br/>" +
                "<div class='post'>" + matchLinksHTML + "</div>" +
                "</p>";

        } else {
            return "<p>" +
                "<span class='header'>Netid:</span>" + submission.student.netid + "" +
                "</p><p>" +
                "<span class='header'>Program:</span>" + studentProgram +
                "</p><p>" +
                "<span class='header'>Status:</span>" + studentStatus +
                "</p><p>" +
                "<span class='header'>History Link:</span><br/>" +
                "<a class='post' target='_newtab' href='" + submission.student.history_link + "'>View Student History</a>" +
                "</p><p>" +
                "<span class='header'>Cross Semester Matches:</span><br/>" +
                "<div class='post'>" + matchLinksHTML + "</div>" +
                "</p>";
        }
    }
}