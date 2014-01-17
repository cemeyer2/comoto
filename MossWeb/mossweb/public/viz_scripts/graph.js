// The actual match & submission data
var matches;
var submissions;

// The list of ids of submissions currently on the submissions list
var submissionIdsOnList = [];

/**
 * Initially load the graph
 *
 * @param matchesParam       The match data from CoMoTo
 * @param submissionsParam   The submission data from CoMoTo
 */
function loadGraph(matchesParam, submissionsParam) {

    // Build the specific data structures for the graph & render it
    matches = convertMatches(matchesParam);
    submissions = submissionsParam;
    submissionIdsOnList = [];
    updateGraph();
}


/**
 * Convert the matches from the API (given in lists of types of matches) to a single list
 *  @param matches  The dictionary of lists of matches from the API
 */
function convertMatches(matches) {

    var formattedMatches = [];

    // Collect same semester matches
    var sameSemesterMatches = matches['sameSemesterMatches'];
    for (var i in sameSemesterMatches) {
        if (sameSemesterMatches.hasOwnProperty(i)) {
            var match = sameSemesterMatches[i];
            match.isSolutionMatch = false;
            match.isCrossSemesterMatch = false;
            formattedMatches.push(match);
        }
    }

    // Collect cross-semester matches
    var crossSemesterMatches = matches['crossSemesterMatches'];
    for (var i in crossSemesterMatches) {
        if (crossSemesterMatches.hasOwnProperty(i)) {
            var match = crossSemesterMatches[i];
            match.isSolutionMatch = false;
            match.isCrossSemesterMatch = true;
            formattedMatches.push(match);
        }
    }

    // Collect solution matches
    var solutionMatches = matches['solutionMatches'];
    for (var i in solutionMatches) {
        if (solutionMatches.hasOwnProperty(i)) {
            var match = solutionMatches[i];
            match.isSolutionMatch = true;
            match.isCrossSemesterMatch = false;
            formattedMatches.push(match);
        }
    }
    return formattedMatches;
}


/**
 * Re-render the graph using the current match & submission data
 */
function updateGraph() {

    // Clear existing graph
    $("#chart svg").remove();

    // Render graph
    var data = buildGraphData();
    renderGraph(data);

    // Disable 'update graph' button
    $('#updateGraphButton').attr('disabled', true);
}


/**
 * Helper function to build the submissions data for the graph
 *
 * @param submissionNodesIndexIndex dictionary to populate with a map containing submissions and their indices
 * @param submissionNodes           list to populate with the submissions
 */
function buildSubmissionData(submissionNodesIndexIndex, submissionNodes) {

    var currentIndex = 0;

    for (var submissionIndex in submissions) {
        if (submissions.hasOwnProperty(submissionIndex)) {

            var submission = submissions[submissionIndex];

            var groupId = submission['type'] === 'solutionsubmission' ? -1 : submission['offering_id'];

            // Create the new node
            var newSubmissionNode = {

                // Group the nodes for coloring by offering
                group:groupId,

                // Store the index of this node in the list
                index:currentIndex,

                // Flags for the type of matches this submission is associated with
                hasSolutionMatch:false,
                hasCrossSemesterMatch:false,

                // Auxiliary stored data for this submission
                id:submission['id'],
                offering_id:submission['offering_id'],
                analysis_pseudonym_ids:submission['analysis_pseudonym_ids'],
                submission_file_ids:submission['submission_file_ids'],
                partner_ids:submission['partner_ids'],
                type:submission['type'],
                student:submission['student'],

                // The indices of all adjacent edges
                edges:[]
            };

            // Insert this new node into both a list & index
            submissionNodesIndexIndex[newSubmissionNode['id']] = currentIndex;
            submissionNodes.push(newSubmissionNode);
            currentIndex += 1;
        }
    }
}


/**
 * Helper function to build the match data for the graph
 *
 * @param submissionNodesIndexIndex dictionary to populate with a map containing submissions and their indices
 * @param submissionNodes           list populated with the submissions
 * @param matchEdges                list to populate with the match objects
 */
function buildMatchData(submissionNodesIndexIndex, submissionNodes, matchEdges) {

    var currentIndex = 0;

    for (var matchIndex in matches) {
        if (matches.hasOwnProperty(matchIndex)) {

            var match = matches[matchIndex];

            // Get the indices the submission ids
            var submission1Index = submissionNodesIndexIndex[match['submission_1_id']];
            var submission2Index = submissionNodesIndexIndex[match['submission_2_id']];

            // Add this edge to adjacencies of submissions
            var submission1 = submissionNodes[submission1Index];
            var submission2 = submissionNodes[submission2Index];

            // Mark the associated submissions as having certain types of matches
            if (match.isCrossSemesterMatch) {
                submission1.hasCrossSemesterMatch = true;
                submission2.hasCrossSemesterMatch = true;
            }
            if (match.isSolutionMatch) {
                submission1.hasSolutionMatch = true;
                submission2.hasSolutionMatch = true;
            }

            // Add match edge indices to corresponding submissions
            submission1.edges.push(currentIndex);
            submission2.edges.push(currentIndex);

            // Determine whether or not this edge represents a match between partners (in either direction)
            var studentOnePartneredTwo = $.inArray(submission2.id, submission1.partner_ids) >= 0;
            var studentTwoPartneredOne = $.inArray(submission1.id, submission2.partner_ids) >= 0;
            var isPartnerMatch = studentOnePartneredTwo || studentTwoPartneredOne;

            // Add the edge
            matchEdges.push({

                // Submission ids (of graph node endpoints)
                source:submission1Index,
                target:submission2Index,
                value:(match['score1'] + match['score1']) / 2.0, // Use average for weight

                // Information about the type of the edge
                isPartnerMatch:isPartnerMatch,
                isSolutionMatch:match.isSolutionMatch,
                isCrossSemesterMatch:match.isCrossSemesterMatch,

                // Auxiliary data for this match
                id:match['id'],
                link:match['link'],
                moss_analysis_id:match['moss_analysis_id'],
                score1:match['score1'],
                score2:match['score2']
            });
            currentIndex++;
        }
    }
}


/**
 * Build the submission data that satisfies the control predicates
 */
function buildSubmissionDataToInclude(submissionNodes, submissionNodesToIncludeIndexIndex, submissionNodesToInclude, matches) {
    var currentIndex = 0;
    for (var submissionIndex in submissionNodes) {
        if (submissionNodes.hasOwnProperty(submissionIndex) && submissionSatisfiesPredicates(submissionNodes[submissionIndex], matches)) {

            var submissionNode = submissionNodes[submissionIndex];

            // Collect all cross-semester matches for this node
            submissionNode.crossSemesterMatches = [];
            for (var i in submissionNode.edges) {
                if (submissionNode.edges.hasOwnProperty(i)) {
                    var match = matches[submissionNode.edges[i]];
                    if (match.isCrossSemesterMatch) {
                        submissionNode.crossSemesterMatches.push(match);
                    }
                }
            }

            submissionNode.edges = [];

            // Insert this new node into both a list & index
            submissionNodesToIncludeIndexIndex[submissionNode['id']] = currentIndex;
            submissionNodesToInclude.push(submissionNode);

            currentIndex++;
        }
    }
}


/**
 * Build the match data that satisfies the control predicates
 */
function buildMatchDataToInclude(matchEdges, submissionNodesToIncludeIndexIndex, submissionNodes,
                                 submissionNodesToInclude, matchEdgesToInclude) {
    var currentIndex = 0;
    for (var matchIndex in matchEdges) {
        if (matchEdges.hasOwnProperty(matchIndex) && matchSatisfiesPredicates(matchEdges[matchIndex])) {

            var matchEdge = matchEdges[matchIndex];

            // Get the indices the submission ids
            var submission1Index = submissionNodesToIncludeIndexIndex[submissionNodes[matchEdge.source].id];
            var submission2Index = submissionNodesToIncludeIndexIndex[submissionNodes[matchEdge.target].id];

            // Add this edge to adjacencies of submissions
            var submission1 = submissionNodesToInclude[submission1Index];
            var submission2 = submissionNodesToInclude[submission2Index];

            // Add match edge indices to corresponding submissions
            submission1.edges.push(currentIndex);
            submission2.edges.push(currentIndex);

            matchEdge.source = submission1Index;
            matchEdge.target = submission2Index;
            matchEdgesToInclude.push(matchEdge);

            currentIndex++;
        }
    }
}


/**
 * Build the graph data structures from the input submission and match data from the API, using the configuration options
 */
function buildGraphData() {

    // Create the restructured matches & submissions to dump to JSON
    var matchEdges = [];
    var submissionNodes = [];

    // Maps submission ids to indices in the list
    var submissionNodesIndexIndex = {};

    // Insert the matches into 'submissionNodes' indexed by submission_id
    buildSubmissionData(submissionNodesIndexIndex, submissionNodes);

    // Insert the matches into 'matchEdges'
    buildMatchData(submissionNodesIndexIndex, submissionNodes, matchEdges);

    var matchEdgesToInclude = [];
    var submissionNodesToInclude = [];
    var submissionNodesToIncludeIndexIndex = {};

    // Filter our matches & submissions to build graph data to display
    buildSubmissionDataToInclude(submissionNodes, submissionNodesToIncludeIndexIndex, submissionNodesToInclude, matchEdges);
    buildMatchDataToInclude(matchEdges, submissionNodesToIncludeIndexIndex, submissionNodes, submissionNodesToInclude, matchEdgesToInclude);

    return {
        nodes: submissionNodesToInclude,
        links: matchEdgesToInclude
    };
}


/**
 * Function to determine whether or not a submission adheres to the predicates defined by the graph controls.
 *  @param  submission              The submission in question
 *  @return Whether or not all predicates are satisfied
 */
function submissionSatisfiesPredicates(submission, matches) {

    var isSolution = submission['type'] === 'solutionsubmission';

    // Check that this submission should be included based on past semester restrictions
    var pastSemestersPredicate = graphControls.includePastSemesters || submission.offering_id === currentOfferingId;

    // Check that this submission should be included based on singletons requirement
    var singletonsPredicate = null;
    if(matches) {


        // Count up the number of edges/matches that satisfy their predicates
        var matchesSatisfyingPredicate = 0;
        for(var i in submission.edges) {
            if(submission.edges.hasOwnProperty(i)) {

                // Check the average weight predicate
                var match = matches[submission.edges[i]];
                var minimumEdgeWeightPredicate = graphControls.minimumEdgeWeight <= (match['score1'] + match['score1']) / 2;
                if(minimumEdgeWeightPredicate) {
                    matchesSatisfyingPredicate++;
                }
            }
        }

        // If we got some matches data, check that there are some matches satisfying predicates or that we can include singletons
        singletonsPredicate = graphControls.includeSingletons || matchesSatisfyingPredicate;

    } else {

        // If we didn't get any matches data, check that there are some edges in general
        singletonsPredicate = graphControls.includeSingletons || submission.edges.length > 0;
    }

    // Check that this is either a solution that should be included, or satisfies all submission predicates
    if (isSolution) {
        return graphControls.includeSolution;
    } else {
        return pastSemestersPredicate && singletonsPredicate;
    }
}


/**
 * Function to determine whether or not a match adheres to the predicates defined by the graph controls
 * @param match The match in question
 */
function matchSatisfiesPredicates(match) {

    // Check if this match's weight is above the minimum edge weight
    var averageWeight = (match['score1'] + match['score1']) / 2; // Use average weight
    var minimumEdgeWeightPredicate = graphControls.minimumEdgeWeight <= averageWeight;

    // Check that this match satisfies the 'include solution' condition
    var solutionPredicate = graphControls.includeSolution || !match.isSolutionMatch;

    // Check that this match satisfies the 'include partner edges' predicate
    var partnerEdgesPredicate = graphControls.includePartnerEdges || !match.isPartnerMatch;

    // Check that this match satisfies the cross-semester matches predicate
    var crossSemesterEdgesPredicate = graphControls.includePastSemesters || !match.isCrossSemesterMatch;

    return minimumEdgeWeightPredicate && solutionPredicate && partnerEdgesPredicate && crossSemesterEdgesPredicate;
}