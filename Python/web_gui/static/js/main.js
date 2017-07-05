// ===== Scroll to Top Arrow ====
var scrollTrigger = 150; // px
var returnToTopElement = $('#return-to-top');
backToTop = function () {
    var scrollTop = $(window).scrollTop();
    if (scrollTop > scrollTrigger) {
        $('#return-to-top').addClass('show');
    } else {
        $('#return-to-top').removeClass('show');
    }
};
backToTop();
$(window).on('scroll', function () {
    backToTop();
});
$('#return-to-top').on('click', function (e) {
    e.preventDefault();
    $('html,body').animate({
        scrollTop: 0
    }, 700);
});

var BouncesGUIControls = {
    init: function () {
        this.bindUIActions();
    },
    bindUIActions: function () {
        var that = this;
        // Any buttons with a bounce-id data attr are presumed to be a play button
        // Clicking it will be the bounce with the specified id. *arm emoji*
        $('.js-play_bounce').on('click', function () {
            var bounce_id = $(this).data("bounce-id");
            var compare_to_ideal = $(this).data("compare-to-ideal");
            $.post({
                url: SCRIPT_ROOT + "/play_bounce",
                data: "bounce_id=" + bounce_id
                + "&compare_to_ideal=" + compare_to_ideal,
                dataType: "text",
                success: function (data) {
                    if (data.length === 0) {
                    }
                    else {
                        console.log(data);
                    }
                }
            });
        });

        // Hover Actions
        $('.js-bounce img').on('click', function () {
            if ($(this).data('continue-playing')) {
                $(this).data('continue-playing', false)
            }
            else {
                $(this).data('continue-playing', true)
            }
        });

        $('.js-bounce img').hover(
            function () {
                var src = $(this).attr("src");
                $('.js-angles').attr("src", src.replace(/\.jpg|\.gif$/i, "_angles.jpg"));

                if (!$(this).data('continue-playing')) {
                    $(this).attr("src", src.replace(/\.jpg$/i, ".gif"));
                }
            },
            function () {
                if (!$(this).data('continue-playing')) {
                    var src = $(this).attr("src");
                    $(this).attr("src", src.replace(/\.gif$/i, ".jpg"));
                }
            }
        );

        // Deduction Inter-Actions
        $('.js-add_deductions').on('click', function () {
            var $thisBtn = $(this);
            $thisBtn.text('Saving...');
            // Get the current deduction categories container el
            // On the same level as the button
            var $thisDeductionCategories = $(this).siblings('.js-deduction_categories');
            var bounce_id = $thisDeductionCategories.data('bounce-id');

            // Loop through the categories, i.e. arms legs body
            var bounceDeductionsJSON = that.getDeductionsJSON($thisDeductionCategories);
            var deductionsValue = that.deductionsToScore(bounceDeductionsJSON);

            // Send deductions to the sever
            $.post({
                url: SCRIPT_ROOT + "/judge_bounce",
                data: "bounce_id=" + bounce_id
                + "&bounce_deductions_value=" + deductionsValue
                + "&bounce_deductions_json=" + JSON.stringify(bounceDeductionsJSON),
                dataType: "text",
                success: function (data) {
                    if (data.length === 0) {
                        $thisBtn.text('Saved!');
                    }
                    else {
                        $thisBtn.text('Not Saved');
                        console.log(data);
                    }
                }
            });
        });

        $('.js-deduction_category :input').on('change', function () {
            // Get the current deduction categories container el, and its score value element
            var $thisDeductionCategories = $(this).parents('.js-deduction_categories');
            var $deductionValue = $thisDeductionCategories.siblings('.js-new_deduction_value');

            // Loop through the categories, i.e. arms legs body
            var skillDeductions = that.getDeductionsJSON($thisDeductionCategories);
            var deductionValue = that.deductionsToScore(skillDeductions);

            // Update the displayed deduction
            $deductionValue.text(deductionValue.toFixed(1));
        });
    },
    getDeductionsJSON: function ($deductionCategories) {
        var skillDeductions = {};
        $deductionCategories.each(function () {
            // Get the checked item(s) in this category
            var $incurredDeductions = $(this).find(':checked');
            // Add each one of them that's checked (Legs can have multiple independent deductions)
            $incurredDeductions.each(function () {
                var deduction_cat_name = $(this).attr('name').replace(/-\d+/, '');
                skillDeductions[deduction_cat_name] = $(this).val();
            });
        });
        return skillDeductions
    },
    deductionsToScore: function (skillDeductions) {
        var maxDeductions = {
            'arms': 0.1,
            'legs': 0.2,
            'body': 0.2,
            'openingKeepingStraight': 0.3
        };
        var theseDeductions = {
            'arms': 0.0,
            'legs': 0.0,
            'body': 0.0,
            'openingKeepingStraight': 0.0
        };

        var deductionKeys = Object.keys(skillDeductions);
        for (var i = 0; i < deductionKeys.length; i++) {
            var deductionKey = deductionKeys[i];
            if (deductionKey.includes('shape'))
                continue;

            if (deductionKey.includes('arms')) {
                theseDeductions['arms'] += parseFloat(skillDeductions[deductionKey])
            }
            else if (deductionKey.includes('legs')) {
                theseDeductions['legs'] += parseFloat(skillDeductions[deductionKey])
            }
            else if (deductionKey.includes('body')) {
                theseDeductions['body'] += parseFloat(skillDeductions[deductionKey])
            }
            else if (deductionKey.includes('opening') || deductionKey.includes('timing')) {
                theseDeductions['openingKeepingStraight'] += parseFloat(skillDeductions[deductionKey])
            }
            else {
                // Line out/Horz angle of legs
                theseDeductions[deductionKey] = parseFloat(skillDeductions[deductionKey])
            }
        }

        var deductionTally = 0;
        var theseKeys = Object.keys(theseDeductions);
        for (var i = 0; i < theseKeys.length; i++) {
            var deductionKey = theseKeys[i];
            if (maxDeductions.hasOwnProperty(deductionKey)) {
                deductionTally += Math.min(theseDeductions[deductionKey], maxDeductions[deductionKey])
            }
            else {
                deductionTally += theseDeductions[deductionKey]
            }
        }

        return Math.min(deductionTally, 0.5);
    }
};


var RoutinesGUIControls = {
    init: function () {
        this.bindUIActions();
    },
    bindUIActions: function () {
        $('button').on('click', this.handleAction);
        $('.level-select').on('change', this.setLevel)
    },
    setLevel: function () {
        var level = $(this).val();
        var routineId = $(this).closest('.card').data('routineid');

        // Send to server
        $.post({
            url: SCRIPT_ROOT + "/set_level",
            data: "&routine_id=" + routineId
            + "&level=" + level,
            dataType: "text"
        });
    },
    handleAction: function () {
        var routineId = $(this).closest('.card').data('routineid');

        if ($(this).hasClass('js-namer')){
            var name = $(this).siblings('.namer_input').val();

            // Send to server
            $.post({
                url: SCRIPT_ROOT + "/namer",
                data: "&routine_id=" + routineId
                + "&name=" + name,
                dataType: "text",
                success: function (data) {
                    if (data.length === 0) {
                        $(this).text('Saved')
                    }
                    else {
                        alert(data);
                        console.log(data);
                    }
                }
            });
            return
        }

        var action = $(this).data('action');

        if (action === 'delete_pose') {
            isSure = confirm('Are you sure you want to detele the pose on this routine?');
            if (!isSure) {
                // Don't do anything
                return
            }
        }

        // Send to server
        $.post({
            url: SCRIPT_ROOT + "/gui_action",
            data: "&routine_id=" + routineId
            + "&action=" + action,
            dataType: "text",
            success: function (data) {
                if (data.length === 0) {
                }
                else {
                    alert(data);
                    console.log(data);
                }
            }
        });
    }
};


var Label = {
    bounces: [],
    skillNames: select2SkillNameData, // imported from js file

    init: function (routineId, bounceIds, bounceNames) {
        this.routineId = routineId;
        this.bounceIds = bounceIds;
        this.bounceNames = bounceNames;

        this.select2Setup();

        this.bindUIActions();

        // Set focus on the first loop button
        $('.js-loop-btn').eq(0).focus()
    },
    select2Setup: function () {
        var that = this;

        // Set up select2 inputs
        // http://stackoverflow.com/questions/16907825/how-to-implement-sublime-text-like-fuzzy-search
        $.fn.select2.amd.require(['select2/compat/matcher'], function (oldMatcher) {
            $(".js-select2").select2({
                data: that.skillNames,
                matcher: oldMatcher(that.fuzzyMatcher)
            })
            // Any time the select2 dropdown is closed, give it focus. otherwise focus disappears, which sucks
                .on("select2:close", function () {
                    $(this).focus();
                })
                .on("select2:select", function () {
                    window.onbeforeunload = confirmOnPageExit;
                })
                .each(function (i) {
                    if (that.bounceNames[i] !== '')
                        this.value = that.bounceNames[i]
                })
                .trigger('change');
        });
    },
    fuzzyMatcher: function (search, text) {
        search = search.toUpperCase();
        text = text.toUpperCase();

        var j = -1; // remembers position of last found character

        // consider each search character one at a time
        for (var i = 0; i < search.length; i++) {
            var l = search[i];
            if (l == ' ') continue;     // ignore spaces

            j = text.indexOf(l, j + 1);     // search for character & update position
            if (j == -1) return false;  // if it's not found, exclude this item
        }
        return true;
    },
    shiftUp: function () {
        for (var i = 0; i < this.bounceNames.length - 1; i++) {
            $(".js-select2")[i].value = $(".js-select2")[i + 1].value
        }
        // Update all
        $(".js-select2").trigger('change');
    },
    shiftDown: function () {
        for (var i = this.bounceNames.length - 2; i >= 0; i--) {
            $(".js-select2")[i + 1].value = $(".js-select2")[i].value
        }
        // Update all
        $(".js-select2").trigger('change');
    },
    bindUIActions: function () {
        // var that = this;

        $('.js-save').on('click', this.save);
    },
    save: function () {
        var that = Label;

        $('.js-save').text('Saving...');

        // Get the names for each skill
        for (var i = 0; i < $(".js-select2").length; i++) {
            that.bounceNames[i] = $(".js-select2")[i].value
        }

        // Send to server
        $.post({
            url: SCRIPT_ROOT + "/label",
            data: "&id=" + that.routineId
            + "&bounceIds=" + JSON.stringify(that.bounceIds)
            + "&bounceNames=" + JSON.stringify(that.bounceNames),
            dataType: "text",
            success: function (data) {
                if (data.length === 0) {
                    $('.js-save').text('Saved!');

                    window.onbeforeunload = null;
                }
                else {
                    $('.js-save').text('Not Saved');

                    console.log(data);
                }
            }
        });

    }
};


var Judge = {
    init: function (routineId, skillIds) {
        this.routineId = routineId;
        this.skillIds = skillIds;

        // Cache jQuery selectors
        this.$js_score = $('.js-score');
        this.$save = $('.js-save');
        this.$deductionValues = $('.js-deduction_value');

        // Array of arrays where each top-lvl array represents a skill row and 2nd-lvl represents all deduction elements for that skill
        var that = this;
        this.skillsDeductionCategories = [];
        var skillRows = $('.js-deduction_categories');
        skillRows.each(function () {
            that.skillsDeductionCategories.push(
                $(this).find('.js-deduction_category')
            );
        });

        // Figure out the number of skills and cap it at 10 for calculating the score
        this.numSkills = this.$deductionValues.length;
        this.numSkillsScoreable = Math.min(this.numSkills, 10); // pick the smaller of the two

        this.bindUIActions();
    },
    bindUIActions: function () {
        that = this;

        $('.js-after_opening').on('change', function () {
            var $deductionRadios = $(this).parent()
                .parent()
                .find(':input') // Get all inputs in this row
                .not('.js-after_opening'); // Which aren't the Tuck/Pike selection buttons

            var isTuck = $(this).val() == "tuck";
            var offset = isTuck ? 1 : 0;
            var find = isTuck ? 'pike' : 'tuck';
            var replace = isTuck ? 'tuck' : 'pike';

            $deductionRadios.each(function (i) {
                var val = '0.0';
                var $thisDedLabel = $(this).parent();
                // For the 2nd and 3rd radios, change their label text and val.
                if (i > 0) {
                    val = ((i + offset) / 10).toFixed(1);
                    $thisDedLabel.children('.js-val').text(val);
                    $(this).attr('value', val);
                    $(this).val(val);
                }
                // Change input name
                var newName = $(this).attr('name').replace(find, replace); // replace tuck with pike
                $(this).attr('name', newName);

                // Change the tooltip image
                var tooltipHTML = $thisDedLabel.attr('data-original-title')
                    .replace(find, replace) // replace tuck with pike
                    .replace(/0\.\d/g, val);// replace deduction value appropriately
                $thisDedLabel.attr('data-original-title', tooltipHTML);
            })
        });

        $('.js-deduction_category :input').on('change', function () {
            // Register a "sure-you-wanna-leave" dialog when first clicked (but also every time after)
            window.onbeforeunload = confirmOnPageExit;

            var $thisBounceRow = $(this).parents('.js-bounce');
            var skillIndex = $('.js-bounce').index($thisBounceRow);
            var deduction = 0;

            // Check for input on "Landing"s which are handled differently to other skills by comparing skillIndex to the number of skills
            // Landing will always be last
            if (skillIndex == that.numSkills - 1) {
                deduction = that.tallyLandingDeductions(skillIndex);
            }
            else {
                deduction = that.tallySkillDeductions(skillIndex);
            }

            // Update the displayed deduction
            $(that.$deductionValues[skillIndex]).text(deduction.toFixed(1));

            that.calculateScore()
        });

        // Visually/Interactively enforce the mutual constrain of "opening timing" and "keeping shape after opening"
        $('input[name*="opening_timing"]').on('change', function () {
            var $afterOpeningRadios = $(this).parent() // label
                .parent() // .pull-right
                .parent() // .js-deduction_category
                .next() // .js-deduction_category
                .children('.pull-right')
                .find(':input');

            var openingDeduction = $(this).val();
            if (openingDeduction == '0.0' || openingDeduction == '0.1') {
                $afterOpeningRadios.prop('disabled', false);
            }
            else if (openingDeduction == '0.2') {
                $afterOpeningRadios.eq(0).prop('disabled', false); // 0 = 0.0
                $afterOpeningRadios.eq(1).prop('disabled', false); // 1 = 0.1
                $afterOpeningRadios.eq(2).prop('checked', false)
                    .prop('disabled', true); // 2 = 0.2
            }
            else if (openingDeduction == '0.3') {
                $afterOpeningRadios.prop('checked', false).prop('disabled', true);
            }
        });

        that.$save.click(that.save);
    },
    tallySkillDeductions: function (skillIndex) {
        var skillDeductions = this.collectSkillDeductions(skillIndex);
        // // Rotation/Flying Phase
        // positionArms  // elbows, swinging (shoulders), angle to stop twist
        // positionLegs  // knees, toes, legs not together
        // positionBody  // hips, dishedness
        // // Opening and Landing Phase
        // keepingStraightPosition  // pike down, tuck down, twist rotation
        // opening

        var maxDeductions = {
            'arms': 0.1,
            'legs': 0.2,
            'body': 0.2,
            'openingKeepingStraight': 0.3
        };
        var theseDeductions = {
            'arms': 0.0,
            'legs': 0.0,
            'body': 0.0,
            'openingKeepingStraight': 0.0
        };
        var deductionKeys = Object.keys(skillDeductions);
        for (var i = 0; i < deductionKeys.length; i++) {
            var deductionKey = deductionKeys[i];
            if (deductionKey.includes('shape'))
                continue;

            if (deductionKey.includes('arms')) {
                theseDeductions['arms'] += parseFloat(skillDeductions[deductionKey])
            }
            else if (deductionKey.includes('legs')) {
                theseDeductions['legs'] += parseFloat(skillDeductions[deductionKey])
            }
            else if (deductionKey.includes('body')) {
                theseDeductions['body'] += parseFloat(skillDeductions[deductionKey])
            }
            else if (deductionKey.includes('opening') || deductionKey.includes('timing')) {
                theseDeductions['openingKeepingStraight'] += parseFloat(skillDeductions[deductionKey])
            }
            else {
                // Line out/Horz angle of legs
                theseDeductions[deductionKey] = parseFloat(skillDeductions[deductionKey])
            }
        }

        var deductionTally = 0;
        var theseKeys = Object.keys(theseDeductions);
        for (var i = 0; i < theseKeys.length; i++) {
            var deductionKey = theseKeys[i];
            if (maxDeductions.hasOwnProperty(deductionKey)) {
                deductionTally += Math.min(theseDeductions[deductionKey], maxDeductions[deductionKey])
            }
            else {
                deductionTally += theseDeductions[deductionKey]
            }
        }

        return Math.min(deductionTally, 0.5);
    },
    tallyLandingDeductions: function (skillIndex) {
        var obDeductions = this.collectSkillDeductions(skillIndex);

        var landingDeductionTally = 0;
        var remainingKeys = Object.keys(obDeductions);
        for (var i = 0; i < remainingKeys.length; i++) {
            var deductionKey = remainingKeys[i];
            landingDeductionTally += parseFloat(obDeductions[deductionKey]);
        }

        return Math.min(landingDeductionTally, 0.2)
    },
    calculateScore: function () {
        var totalDeductions = 0;
        for (var i = 0; i < this.numSkills; i++) {
            totalDeductions += parseFloat($(this.$deductionValues[i]).text())
        }
        var score = this.numSkillsScoreable - totalDeductions;
        this.$js_score.text(score.toFixed(1));
    },
    collectSkillDeductions: function (skillIndex) {
        var skillDeductions = {}; // Object to hold all deductions of this row.

        // Loop through the categories, i.e. arms legs body
        var $thisSkillDeductionCats = $(this.skillsDeductionCategories[skillIndex]);
        $thisSkillDeductionCats.each(function () {
            // Get the checked item(s) in this category
            var $incurredDeductions = $(this).find(':checked');
            // Add each one of them that's checked (Legs can have multiple independent deductions)
            $incurredDeductions.each(function () {
                var deduction_cat_name = $(this).attr('name').replace(/-\d+/, '');
                skillDeductions[deduction_cat_name] = $(this).val();
            });
        });
        // In the context of a routine with straight Bounces removed, bounces are referred to as skills to differentiate. This is probably confusing...
        return skillDeductions
    },
    collectRoutineDeductions: function () {
        var routine_deductions = []; // Array of objects, each object representing a skill row.
        for (var i = 0; i < that.numSkills; i++) {  // Loop through each skill row
            var skillDeductions = this.collectSkillDeductions(i);
            routine_deductions.push(skillDeductions);
        }
        console.log(routine_deductions);
        return routine_deductions;
    },
    save: function () {
        var that = Judge;
        var $username = $('.js-username');
        var username = $username.val().trim();
        if (username === "") {
            alert('Please enter your name before saving. Thank you.');
            $username.focus();
            return;
        }

        that.$save.text('Saving...');

        var routineDeductionsJSON = that.collectRoutineDeductions();
        // Get deduction values
        var routineDeductionValues = [];
        for (var i = 0; i < that.numSkills; i++) {
            routineDeductionValues.push(
                parseFloat($(that.$deductionValues[i]).text())
            )
        }

        // Send to server
        $.post({
            url: SCRIPT_ROOT + "/judge",
            data: "routine_id=" + that.routineId
            + "&username=" + username
            + "&has_categories=new"
            + "&skill_ids=" + JSON.stringify(that.skillIds)
            + "&routine_deduction_values=" + JSON.stringify(routineDeductionValues)
            + "&routine_deductions_json=" + JSON.stringify(routineDeductionsJSON),
            dataType: "text",
            success: function (data) {
                if (data.length === 0) {
                    that.$save.text('Saved!');
                    // Allow navigation away without warning
                    window.onbeforeunload = null;
                }
                else {
                    that.$save.text('Not Saved');
                    console.log(data);
                }
            }
        });
    },
};


var OldJudge = {
    init: function (routineId, skillIds) {
        this.routineId = routineId;
        this.skillIds = skillIds;

        this.bindUIActions();

        // Autofocus the first input
        $('.js-deduction')[0].focus();
    },
    bindUIActions: function () {
        that = this;
        // Number input validation
        $('.js-deduction').on('input', function (e) {
            window.onbeforeunload = confirmOnPageExit;

            that.validateNumber($(this));

            that.calculateScore();
        });

        $('.js-save').click(that.save);
    },
    validateNumber: function ($thatNumberInput) {
        val = $thatNumberInput.val();

        if (val.includes('.')) {
            val = parseInt(val);
            val = (isNaN(val)) ? "0" : val; // is NaN is val<1, i.e. '0.4'
            $thatNumberInput.val(val);
        }
        else if (val < 0) {
            $thatNumberInput.val("0");
        }
        else if (val > 5) {
            $thatNumberInput.val("5");
        }
    },
    calculateScore: function () {
        var numBounces = $('.js-deduction').length;
        numBounces = Math.min(numBounces, 10);
        var totalDeductions = 0;
        for (var i = 0; i < numBounces; i++) {
            totalDeductions += parseInt($('.js-deduction')[i].value) / numBounces;
        }

        var score = numBounces - totalDeductions;
        $('.js-score').text(score.toFixed(1));
    },
    save: function () {
        var that = OldJudge;

        var $username = $('.js-username');
        var username = $username.val().trim();
        if (username === "") {
            alert('Please enter your name before saving. Thank you.');
            $username.focus();
            return;
        }

        $('.js-save').text('Saving...');

        // Get the deductions for all skills
        var deductionsIndex = 0; // separate index thanks to the ...
        var routineDeductionValues = [];
        var routineDeductionsJSON = [];
        for (var i = 0; i < that.skillIds.length; i++) {
            var score = ($(".js-deduction")[deductionsIndex].value / 10).toFixed(1);
            deductionsIndex++;
            routineDeductionValues.push(score);
            routineDeductionsJSON.push(null);
        }

        // Send to server


        $.post({
            url: SCRIPT_ROOT + "/judge",
            data: "routine_id=" + that.routineId
            + "&username=" + username
            + "&has_categories=old"
            + "&skill_ids=" + JSON.stringify(that.skillIds)
            + "&routine_deduction_values=" + JSON.stringify(routineDeductionValues)
            + "&routine_deductions_json=" + JSON.stringify(routineDeductionsJSON),
            dataType: "text",
            success: function (data) {
                if (data.length === 0) {
                    $('.js-save').text('Saved!');
                    // Allow navigation away without warning
                    window.onbeforeunload = null;
                }
                else {
                    $('.js-save').text('Not Saved');
                    console.log(data);
                }
            }
        });
    }
};


// Navigate away with unsaved warning
function confirmOnPageExit(e) {
    // If we haven't been passed the event get the window.event
    e = e || window.event;

    var message = 'Any text will block the navigation and display a prompt';

    // For IE6-8 and Firefox prior to version 4
    if (e) {
        e.returnValue = message;
    }

    // For Chrome, Safari, IE8+ and Opera 12+
    return message;
}


// Chart stuff
var Tally = {
    labels: ["0.0", "0.1", "0.2", "0.3", "0.4", "0.5"],
    backgroundColors: [
        'rgba(255, 99, 132, 0.2)',
        'rgba(54, 162, 235, 0.2)',
        'rgba(255, 206, 86, 0.2)',
        'rgba(75, 192, 192, 0.2)',
        'rgba(153, 102, 255, 0.2)',
        'rgba(255, 159, 64, 0.2)'
    ],
    borderColors: [
        'rgba(255,99,132,1)',
        'rgba(54, 162, 235, 1)',
        'rgba(255, 206, 86, 1)',
        'rgba(75, 192, 192, 1)',
        'rgba(153, 102, 255, 1)',
        'rgba(255, 159, 64, 1)'
    ],
    options: {
        scales: {
            yAxes: [{
                ticks: {
                    beginAtZero: true,
                    stepSize: 5,
                    suggestedMax: 30
                }
            }]
        },
        legend: {
            display: false
        }
    },
    init: function () {
        var that = this;

        $('canvas').each(function (index) {
            thisData = $(this).data('chart-data');
            new Chart(this, {
                type: 'bar',
                data: {
                    labels: that.labels,
                    datasets: [{
                        data: thisData,
                        backgroundColor: that.backgroundColors,
                        borderColor: that.borderColors,
                        borderWidth: 1
                    }]
                },
                options: that.options
            });
        });

    }
};


