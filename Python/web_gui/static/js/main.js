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


var Label = {
    bounces: [],
    skillNames: select2SkillNameData,

    init: function (routineId, bounces) {
        this.bounces = bounces;
        this.routineId = routineId;

        this.select2Setup();
        this.select2Preload();

        this.bindUIActions();

    },
    select2Setup: function () {
        var that = this;

        // Set up select2 inputs
        $(".js-select2")
            .select2({
                data: that.skillNames
            })
            // Any time the select2 dropdown is closed, give it focus. otherwise focus disappears, which sucks
            .on("select2:close", function (e) {
                $(this).focus();
            });
    },
    select2Preload: function () {
        // Preload selects with the names for each skill
        for (var i = 0; i < this.bounces.length; i++) {
            if (this.bounces[i].name)
                $(".js-select2")[i].value = this.bounces[i].name;
        }
        // Update all
        $(".js-select2").trigger('change');

    },
    bindUIActions: function () {
        var that = this;

        $('.js-save').click(that.save);

    },
    save: function () {
        var that = Label;

        $('.js-save').text('Saving...');

        // Get the names for each skill
        for (var i = 0; i < $(".js-select2").length; i++) {
            that.bounces[i].name = $(".js-select2")[i].value;
        }

        // Send to server
        $.post({
            url: "includes/ajax.db.php",
            data: "action=updateBounces" +
            "&id=" + that.routineId +
            "&bounces=" + JSON.stringify(that.bounces),
            dataType: "text",
            success: function (data) {
                if (data.length === 0) {
                    $('.js-save').text('Saved!');
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
        this.$js_save = $('.js-save');
        this.deductionScoreOutputs = $('.js-deduction_score');

        // Array of arrays where each top-lvl array represents a skill row and 2nd-lvl represents all deduction elements for that skill
        var that = this;
        this.skillRowsDeductionCategories = [];
        var skillRows = $('.js-deduction_categories');
        skillRows.each(function () {
            that.skillRowsDeductionCategories.push(
                $(this).find('.js-deduction_category')
            );
        });

        // Figure out the number of skills and cap it at 10 for calculating the score
        this.numSkills = this.deductionScoreOutputs.length;
        this.numSkillScores = Math.min(this.numSkills, 10); // pick the smaller of the two

        this.bindUIActions();
    },
    bindUIActions: function () {
        that = this;

        $('.js-deduction_category :input').on('change', function () {
            var row_i = $(this).data('row-index');
            var score = that.tallySkillDeductions(that.skillRowsDeductionCategories[row_i]);
            $(that.deductionScoreOutputs[row_i]).text(score.toFixed(1));

            that.calculateScore()
        });

        that.$js_save.click(that.save);
    },
    tallySkillDeductions: function ($thatSkillDeductionCat) {
        var deductionTally = 0;
        $thatSkillDeductionCat.each(function () {
            var $incurredDeductions = $(this).find(':checked');
            $incurredDeductions.each(function () {
                deductionTally += parseFloat($(this).val());
            });
        });
        return Math.min(deductionTally, 0.5);
    },
    calculateScore: function () {
        var totalDeductions = 0;
        for (var i = 0; i < this.numSkillScores; i++) {
            totalDeductions += parseFloat($(this.deductionScoreOutputs[i]).text())
        }
        var score = this.numSkillScores - totalDeductions;
        this.$js_score.text(score.toFixed(1));
    },
    save: function () {
        var that = Judge;
        $js_username = $('.js-username')
        if ($js_username.val().trim() === "") {
            alert('Please enter your name before saving.');
            $js_username.focus();
            return;
        }

        that.$js_save.text('Saving...');

        // Get all the deductions for all skills
        var routine_deductions = [];
        for (var i = 0; i < that.numSkills; i++) {
            var $thatSkillDeductionCat = $(that.skillRowsDeductionCategories[i]);
            $thatSkillDeductionCat.each(function () {

                var skill_deductions = {};
                skill_deductions['id'] = that.skillIds[i]

                var $incurredDeductions = $(this).find(':checked');
                $incurredDeductions.each(function () {
                    var deduction_cat_name = $(this).attr('name').replace(/-\d+/, '');
                    skill_deductions[deduction_cat_name] = parseFloat($(this).val());
                });

                routine_deductions.push(skill_deductions);
            });
        }
        console.log(routine_deductions);

        // Send to server
        $.post({
            url: "includes/ajax.db.php",
            data: "action=judge" +
            "&id=" + that.routineId +
            "&userName=" + $js_username.val().trim() +
            "&deductions=" + JSON.stringify(routine_deductions),
            dataType: "text",
            success: function (data) {
                if (data.length === 0) {
                    that.$js_save.text('Saved!');
                }
                else {
                    that.$js_save.text('Not Saved');

                    console.log(data);
                }
            }
        });
    }
};

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
