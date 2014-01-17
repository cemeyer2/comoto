/**
 * Generate the HTML content for the title bar of some match popover
 */
function generateMatchPopoverTitle(match) {
    return "<p>" +
        "<span class='header'>Analysis Link:</span><a target='_blank' href='" + match.link + "'>MOSS Comparison</a>" +
    "</p>";
}


/**
 * Generate the HTML content for the main content of some match popover
 */
function generateMatchPopoverContent(match) {
    return "<p>" +
        "<span class='header'>Score 1:</span>" + match.score1 +
        "</p><p>" +
        "<span class='header'>Score 2:</span>" + match.score2 +
        "</p>"
}