// Course data (loaded once authenticated)
var courses = null;
var currentOfferingId = null;
var offerings;

var hostname = window.location.hostname;

// URLs to the CoMoTo API
var COURSE_DATA_URL = "/viz/getCourseData";
var LOAD_ASSIGNMENT_URL = "/viz/getMatchesAndSubmissions";

if(hostname === "comoto.cs.illinois.edu") {
	COURSE_DATA_URL = "/comoto"+COURSE_DATA_URL;
	LOAD_ASSIGNMENT_URL = "/comoto"+LOAD_ASSIGNMENT_URL;
}

/**
 * Fetch all course data accessible by the user
 */
function fetchCourses(postFunc) {

    // Show loading box saying that we're fetching the user's course data
    reportLoadingStatus('Loading course data..');
    showLoadingPopup();

    $.ajax({

        // Submit the AJAX request
        url:COURSE_DATA_URL,
        data:{},
        type:'POST',
        dataType:'json',

        // Gracefully handle login failure, but make this error fatal
        error:function (errorData) {
            reportFatalLoadingError(errorData);
        },

        // Handle login success, response should be course data
        success:function (data) {

            // Initialize the visualization with the JSON response from the server
            //  (this response should contain the list of
            initializeViz(data);
            hideLoadingPopup();
            loadSidebar();

            postFunc();
        }
    });
}


/**
 * Smoothly load the sidebar
 */
function loadSidebar() {

    // Prettify course browser with jQuery treeview
    $("#analysisBrowser").treeview({
        animated:"fast",
        collapsed:true,
        unique:true
    });

    // Dynamically set the width of the sidebars
    $("#left-sidebar, #right-sidebar").height($("#wrapper").height()-10);
    $("#left-sidebar, #right-sidebar").width(0);
    $("#left-sidebar, #right-sidebar, #content").show();
    $("#left-sidebar, #right-sidebar").animate({
            width: 200
        },
        "slow"
    );

    // Initialize the right sidebar (controls)
    initializeControls();
}


/**
 * Initialize the viz with the list of courses
 *
 *  @param data The course data
 */
function initializeViz(data) {

    // Save the course data
    courses = data;
    offerings = {};

    // Build the sidebar list items based on the course, semester, and MP data
    for (var courseIndex in courses) {
        if (courses.hasOwnProperty(courseIndex)) {

            // Get course data & build course HTML
            var course = courses[courseIndex];
            var courseHTML =
                "<li id='courseNode" + course['id'] + "' class='courseNode'>" +
                    "<span class='course'>" + course['name'] + "</span>" +
                    "<ul id='courseOfferingList" + course['id'] + "' class='offeringList'>";
            var coursesAdded = 0;


            // Build the data for all offerings
            for (var offeringIndex in course['offerings']) {

                // Skip nonstandard semester objects
                if (course['offerings'][offeringIndex]['semester']['type'] === "semester") {

                    // Get offering data & create offering node HTML
                    var offering = course['offerings'][offeringIndex];
                    var offeringText = offering['semester']['season'] + ' ' + offering['semester']['year'];
                    var offeringHTML =
                        "<li id='offeringNode" + offering['id'] + "' class='offeringNode'>" +
                            "<span class='offering'>" + offeringText + "</span>" +
                            "<ul id='offeringAssignmentList" + offering['id'] + "' class='assignmentList'>";

                    // Record offering information
                    if(!offerings[offering['id']]) {
                        offerings[offering['id']] = offering;
                    }

                    // Gather semester & assignment data
                    var semester = offering['semester'];
                    var semesterId = semester['id'];
                    var assignments = course['assignments'];

                    var assignmentsAdded = 0;

                    // Add node for each MP
                    for (var assignmentIndex in assignments) {

                        // Check if this assignment is in the semester we're filling out
                        var assignment = assignments[assignmentIndex];
                        if (assignment['moss_analysis_pruned_offering'].hasOwnProperty('semester') &&
                            assignment['moss_analysis_pruned_offering']['semester']['id'] === semesterId) {

                            // Add assignment HTML
                            var assignmentHTML =
                                "<li id='assignmentNode" + assignment['id'] + "' class='assignmentNode' " +
                                        "onclick=loadAssignment(" + assignment['id'] + "," + offering['id'] + ");>" +
                                    "<span class='assignment'>" + assignment['name'] + "</span>" +
                                    "</li>";
                            offeringHTML += assignmentHTML;
                            assignmentsAdded += 1;
                        }
                    }

                    if (assignmentsAdded > 0) {
                        // Add offering HTML
                        offeringHTML += "</ul></li>";
                        courseHTML += offeringHTML;
                        coursesAdded += 1;
                    }
                }
            }

            // Fill in course HTML content & add to DOM
            if (coursesAdded > 0) {
                courseHTML += "</ul></li>";
                $("#analysisBrowser").append(courseHTML);
            }
        }
    }
}


/**
 * Get the match & submission information associated with the given assignment.
 *
 * @param assignmentId  The id of the assignment whose information to fetch
 */
function loadAssignment(assignmentId, offeringId) {

    reportLoadingStatus("Loading data for assignment...");
    showLoadingPopup();

    currentOfferingId = offeringId;

    // Add assignment indicator
    $(".assignmentNode span").removeClass('selected');
    $("#assignmentNode" + assignmentId + " span").addClass('selected');

    $.ajax({

        // Submit data via AJAX
        url: LOAD_ASSIGNMENT_URL,
        data:{
            assignmentId: assignmentId
        },
        type:'POST',
        dataType:'json',

        // Gracefully handle failure
        error: reportLoadingError,

        // Handle login success, response should be course data
        success:function (data) {
            reportLoadingStatus("Generating analysis graph...");
            loadGraph(data['matches'], data['submissions']);
            hideLoadingPopup();
            enableControls();
        }
    });
}
