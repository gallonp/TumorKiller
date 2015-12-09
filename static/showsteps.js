

/**
 * Enable all steps up to and including step N, disable all steps after step N.
 * @param stepsToShow Number of steps N to show.
 * @param sections List of div elements, where each div is a step.
 * @param buttons List of input elements. These are considered the last step
 *     to show.
 */
function showSteps(stepsToShow, sections, buttons) {
    // Show up to current step, hide all next steps.
    console.log("Steps to show: " + stepsToShow);
    var opacity_hidden = 0.5;
    for (var i = 0; i < sections.length; ++i) {
        // Update step visibility.
        var inputs_disabled = false;
        if (i < stepsToShow) {
            // Show this step.
            sections[i].style.opacity = 1;
        } else {
            sections[i].style.opacity = opacity_hidden;
            // Disable inputs.
            inputs_disabled = true;
        }
        // Update buttons.
        var section_inputs = sections[i].getElementsByTagName("input");
        for (var j = 0; j < section_inputs.length; ++j) {
            section_inputs[j].disabled = inputs_disabled;
        }
        var section_selects = sections[i].getElementsByTagName("select");
        for (var j = 0; j < section_selects.length; ++j) {
            section_selects[j].disabled = inputs_disabled;
        }
    }
    // Update form buttons.
    var showFormButtons = (stepsToShow > sections.length);
    for (var i = 0; i < buttons.length; ++i) {
        if (showFormButtons) {
            buttons[i].style.opacity = 1;
            buttons[i].disabled = false;
        } else {
            buttons[i].style.opacity = opacity_hidden;
            buttons[i].disabled = true;
        }
    }
}
