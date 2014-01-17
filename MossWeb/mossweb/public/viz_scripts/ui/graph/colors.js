/**
 * Custom palette for handling node colors
 */
var nodePalette = function () {

    // Adapted from 'd3_category10', entirely cool/neutral colors (exclude warm colors for important nodes)
    return d3.scale.ordinal().range([
        "#1f77b4", // Blue
        "#2ca02c", // Green
        "#9467bd", // Fuscia-purple
        "#e377c2", // Fuscia
        "#7f7f7f", // Gray
        "#17becf"  // Bright-light blue
    ]);
}(); // build the function on including the file


/**
 * Custom fill using palette for handling certain node types explicitly. Special nodes take warm colors, and others take
 *  cool or neutral colors.
 *
 *  @param  submission   The submission for the node to be colored. Group ids:
 *
 *      -1: Solution
 *      0+: Student submission
 */
var fillNode = function(submission) {

    // Check for the solution node
    if (submission.group < 0) {
        return "#8c564b"; // Deep red/purple
    } else {

        // Color the node special colors if it has a solution or past semester match
        if(submission.hasCrossSemesterMatch && submission.hasSolutionMatch) {
            return "#bcbd22"; // Olive-yellow
        } else if (submission.hasCrossSemesterMatch && (submission.offering_id === currentOfferingId)) {
            return "#ff7f0e"; // Orange
        } else if (submission.hasSolutionMatch) {
            return "#d62728"; // Deep red
        } else {
            return nodePalette(submission.group);
        }
    }
};


/**
 * Color the edge appropriately, according to its type
 *  @param  match   The match object corresponding to the edge
 */
var colorMatchEdge = function (match) {
    if (match.isCrossSemesterMatch) {
        return "#ff7f0e"; // Orange
    } else if (match.isSolutionMatch) {
        return "#8c564b"; // Deep red/purple
    } else if (match.isPartnerMatch) {
        return "#2ca02c"; // Green
    } else {
        return ""; // Default gray color for other edges
    }
};