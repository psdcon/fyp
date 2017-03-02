"""
SELECT skill_name, count(1) as c FROM bounces GROUP BY skill_name ORDER BY c DESC
y"In/Out Bounce"	"224"
n"Tuck Jump"	"52"
y"Swivel Hips/Seat Half Twist to Seat Drop"	"46"
y"Straddle Jump"	"43"
y"Pike Jump"	"42"
y"Full Twist Jump"	"39"
y"Back S/S"	"31"
y"Half Twist to Feet (from seat)"	"31"
y"Seat Drop"	"28"
"Broken"	"24"
y"Half Twist Jump"	"23"
y"Back Drop"	"21"
y"Half Twist to Seat Drop"	"18"
""	"16"  <---- blank
y"To Feet (from seat)"	"16"
y"Barani"	"15"
y"Front Drop"	"13"
y"To Feet (from front)"	"12"
y"Front S/S"	"11"
y"To Feet (from back)"	"8"
y"Half Twist to Feet (from back)"	"6"
y"Back S/S to Seat"	"1"
y"Crash Dive"	"1"
y"Lazy Back"	"1"
"""

skill_deductions = {
    'tuck jump, pike jump, straddle jump,': ['arms', 'legs', 'body', 'angle_with_horizontal', 'opening_shape_jumps'],
    'seat drop, To Feet (from seat), to feet (from front), to feet (from back), front drop, back drop': ['arms', 'legs', 'body'],
    'Half Twist to Feet (from back), Half Twist to Seat Drop, Swivel Hips/Seat Half Twist to Seat Drop, Half Twist to Feet (from seat), half twist jump, full twist jump': ['arms', 'legs', 'body', 'twist_timing'],
    'Back S/S, Back S/S to Seat, lazy back, Front S/S': ['arms', 'legs', 'body', 'opening_timing_somi', 'after_opening_feet_front'],
    'crash dive': ['arms', 'legs', 'body', 'opening_timing_somi', 'after_opening_back'],
    'Barani': ['arms', 'legs', 'body', 'opening_timing_somi', 'after_opening_feet_front', 'twist_timing', 'twist_arms_half_full'],
}

judging_rows_html = {

    'arms': """
<div class="js-deduction_category clearfix">
    Arms
    <span class="pull-right">
        <label>
            <input data-row-index={index} type="radio" name="arms-{index}" value="0.1"> 0.1 Elbows
        </label>
        <label>
            <input data-row-index={index} type="radio" name="arms-{index}" value="0.1"> 0.1 Windmilling
        </label>
    </span>
</div>""",

    'legs': """
<div class="js-deduction_category clearfix" title="Bent knees, toes not pointed, legs note">
    Legs
    <span class="pull-right">
        <label>
            <input data-row-index={index} type="checkbox" name="legs_knees" value="0.1"> 0.1 Knees
        </label>
        <label>
            <input data-row-index={index} type="checkbox" name="legs_toes" value="0.1"> 0.1 Toes
        </label>
        <label>
            <input data-row-index={index} type="checkbox" name="legs_apart" value="0.1"> 0.1 Apart
        </label>
    </span>
</div>""",

    # <!-- tighness of shape/dished/angle of hips(pikey) -->
    'body': """
<div class="js-deduction_category clearfix">
    Body
    <span class="pull-right">
        <label>
            <input data-row-index={index} type="radio" name="body-{index}" value="0.1"> 0.1 Loose
        </label>
        <label>
            <input data-row-index={index} type="radio" name="body-{index}" value="0.2"> 0.2 Very loose
        </label>
    </span>
</div>""",

    'angle_with_horizontal': """
<div class="js-deduction_category clearfix">
    Legs with Horizontal
    <span class="pull-right">
        <label data-toggle="tooltip" title="<img src='/static/images/judging/horz_0.0.jpg'>" old_title=">=90&deg;">
            <input data-row-index={index} type="radio" name="legs_horz-{index}" value="0.0"> 0.0
        </label>
        <label data-toggle="tooltip" title="<img src='/static/images/judging/horz_0.1.jpg'>" old_title=">65&deg; <90&deg;">
            <input data-row-index={index} type="radio" name="legs_horz-{index}" value="0.1"> 0.1
        </label>
        <label data-toggle="tooltip" title="<img src='/static/images/judging/horz_0.2.jpg'>" old_title=">45&deg; <65&deg;">
            <input data-row-index={index} type="radio" name="legs_horz-{index}" value="0.2"> 0.2
        </label>
    </span>
</div>""",

    'opening_shape_jumps': """
<div class="js-deduction_category clearfix">
    Opening
    <span class="pull-right">
        <label>
            <input data-row-index={index} type="checkbox" name="line_out" value="0.1"> 0.1 Line out
        </label>
    </span>
</div>""",

    'opening_timing_somi': """
<div class="js-deduction_category clearfix">
    Opening in Somersault
    <span class="pull-right">
        <label data-toggle="tooltip" title="<img src='/static/images/judging/opening_front_0.0.jpg'>" data-oldtitle="Use if you made a mistake">
            <input data-row-index={index} type="radio" name="opening_timing-{index}" value="0.0"> 0.0
        </label>
        <label data-toggle="tooltip" title="<img src='/static/images/judging/opening_front_0.1.jpg'>"" data-oldtitle="bet 1 &amp; 2 o'clock">
            <input data-row-index={index} type="radio" name="opening_timing-{index}" value="0.1"> 0.1
        </label>
        <label data-toggle="tooltip" title="<img src='/static/images/judging/opening_front_0.2.jpg'>" data-oldtitle="bet 2 &amp; 3 o'clock">
            <input data-row-index={index} type="radio" name="opening_timing-{index}" value="0.2"> 0.2
        </label>
        <label data-toggle="tooltip" title="<img src='/static/images/judging/opening_front_0.3.jpg'>"" data-oldtitle="after 3/no opening">
            <input data-row-index={index} type="radio" name="opening_timing-{index}" value="0.3"> 0.3
        </label>
    </span>
</div>""",

    'after_opening_feet_front': """
<div class="js-deduction_category clearfix">
    After Opening in Somersault<br>
    <label>
        <input class="js-after_opening" data-row-index={index} type="radio" name="opening_holding_front_shape-{index}" value="pike" checked> Pike Down
    </label>
    <label>
        <input class="js-after_opening" data-row-index={index} type="radio" name="opening_holding_front_shape-{index}" value="tuck"> Tuck Down
    </label>

    <span class="pull-right">
        <label data-toggle="tooltip" title="<img src='/static/images/judging/after_opening_front_pike_0.0.jpg'>" old_title="bet 2 &amp; 3 o'clock">
            <input data-row-index={index} type="radio" name="opening_holding_front_deduction-{index}" value="0.0"> <span class="js-val">0.0</span>
        </label>
        <label data-toggle="tooltip" title="<img src='/static/images/judging/after_opening_front_pike_0.1.jpg'>" old_title="bet 2 &amp; 3 o'clock">
            <input data-row-index={index} type="radio" name="opening_holding_front_deduction-{index}" value="0.1"> <span class="js-val">0.1</span>
        </label>
        <label data-toggle="tooltip" title="<img src='/static/images/judging/after_opening_front_pike_0.2.jpg'>" old_title="bet 12 &amp; 2 o'clock">
            <input data-row-index={index} type="radio" name="opening_holding_front_deduction-{index}" value="0.2"> <span class="js-val">0.2</span>
        </label>
    </span>
</div>""",

    'after_opening_back': """
<div class="js-deduction_category clearfix">
    After Opening in Somersault<br>
    <label>
        <input class="js-after_opening" data-row-index={index} type="radio" name="opening_holding_back_shape-{index}" value="pike" checked> Pike Down
    </label>
    <label>
        <input class="js-after_opening" data-row-index={index} type="radio" name="opening_holding_back_shape-{index}" value="tuck"> Tuck Down
    </label>

    <span class="pull-right">
        <label data-toggle="tooltip" title="<img src='/static/images/judging/after_opening_back_pike_0.0.jpg'>" old_title="bet 3 &amp; 4:30 o'clock">
            <input data-row-index={index} type="radio" name="opening_holding_back_deduction-{index}" value="0.0"> <span class="js-val">0.0</span>
        </label>
        <label data-toggle="tooltip" title="<img src='/static/images/judging/after_opening_back_pike_0.1.jpg'>" old_title="bet 3 &amp; 4:30 o'clock">
            <input data-row-index={index} type="radio" name="opening_holding_back_deduction-{index}" value="0.1"> <span class="js-val">0.1</span>
        </label>
        <label data-toggle="tooltip" title="<img src='/static/images/judging/after_opening_back_pike_0.2.jpg'>" old_title="bet 12 &amp; 3 o'clock">
            <input data-row-index={index} type="radio" name="opening_holding_back_deduction-{index}" value="0.2"> <span class="js-val">0.2</span>
        </label>
    </span>
</div>""",

    'twist_timing': """
<div class="js-deduction_category clearfix">
    End of Twist
    <span class="pull-right">
        <label data-toggle="tooltip" title="<img src='/static/images/judging/twist_0.0.jpg'>">
            <input data-row-index={index} type="checkbox" name="" value="0.0"> 0.0
        </label>
        <label data-toggle="tooltip" title="<img src='/static/images/judging/twist_0.1.jpg'>">
            <input data-row-index={index} type="checkbox" name="" value="0.1"> 0.1
        </label>
    </span>
</div>""",

    'twist_arms_half_full': """
<div class="js-deduction_category clearfix">
    Arms to Stop Twist
    <span class="pull-right">
        <label data-toggle="tooltip" title="<img src='/static/images/judging/twist_arms_half_full_0.0.jpg'>">
            <input data-row-index={index} type="checkbox" name="" value="0.0"> 0.0
        </label>
        <label data-toggle="tooltip" title="<img src='/static/images/judging/twist_arms_half_full_0.1.jpg'>">
            <input data-row-index={index} type="checkbox" name="" value="0.1"> 0.1
        </label>
    </span>
</div>""",

    'twist_arms_over_full': """
<div class="js-deduction_category clearfix">
    Arms to Stop Twist
    <span class="pull-right">
        <label data-toggle="tooltip" title="<img src='/static/images/judging/twist_arms_rudi_plus_0.0.jpg'>">
            <input data-row-index={index} type="checkbox" name="" value="0.0"> 0.0
        </label>
        <label data-toggle="tooltip" title="<img src='/static/images/judging/twist_arms_rudi_plus_0.1.jpg'>" title="Arms >90&deg;">
            <input data-row-index={index} type="checkbox" name="" value="0.1"> 0.1
        </label>
    </span>
</div>"""
}



#                         {#                        <div class="col-12">#}
# {#                            <div title="Bent elbows">#}
# {#                                Arms <br>#}
# {#                                <input data-row-index={index} type="checkbox" name="" id=""> Bent elbows 0.1#}
# {#                            </div>#}
# {#                            <div title="Bent knees, toes not pointed, legs note">#}
# {#                                Legs - <br>#}
# {#                                <input data-row-index={index} type="checkbox" name="" id=""> Bent knees 0.1#}
# {#                                <input data-row-index={index} type="checkbox" name="" id=""> Toes not pointed 0.1#}
# {#                                <input data-row-index={index} type="checkbox" name="" id=""> Legs not together 0.1#}
# {#                            </div>#}
# {#                            <div>#}
# {#                                Body - tighness of shape/dished/angle of hips(pikey) <br>#}
# {#                                <input data-row-index={index} type="radio" name="body" id=""> Loose shape 0.1#}
# {#                                <input data-row-index={index} type="radio" name="body" id=""> Very loose shape 0.2#}
# {#                            </div>#}
# {#                            <div>#}
# {#                                Angle of legs with Horizontal <br>#}
# {#                                <input data-row-index={index} type="radio" name="horz" id=""> >65&deg; <90&deg; 0.1#}
# {#                                <input data-row-index={index} type="radio" name="horz" id=""> >45&deg; <65&deg; 0.2#}
# {#                            </div>#}
# {#                            <div>#}
# {#                                Opening (shape jumps) <br>#}
# {#                                <input data-row-index={index} type="radio" name="horz" id=""> >65&deg; <90&deg; 0.1#}
# {#                                <input data-row-index={index} type="radio" name="horz" id=""> >45&deg; <65&deg; 0.2#}
# {#                            </div>#}
# {#                            <div>#}
# {#                                Opening timing (somi) for feet/front landing (cody)/back landing <br>#}
# {#                                <input data-row-index={index} type="radio" name="horz" id=""> bet 1 & 2 o'clock 0.1#}
# {#                                <input data-row-index={index} type="radio" name="horz" id=""> bet 2 & 3 o'clock 0.2#}
# {#                                <input data-row-index={index} type="radio" name="horz" id=""> after 3/no opening 0.3#}
# {#                            </div>#}
# {#                            <div>#}
# {#                                Opening holding shape for feet or front. (later is better) <br>#}
# {#                                Person#}
# {#                                <input data-row-index={index} type="radio" name="" id=""> piked down#}
# {#                                <input data-row-index={index} type="radio" name="" id=""> tucked down#}
# {##}
# {#                                <input data-row-index={index} type="radio" name="horz" id=""> bet 12 & 2 o'clock 0.2#}
# {#                                <input data-row-index={index} type="radio" name="horz" id=""> bet 2 & 3 o'clock 0.1#}
# {#                            </div>#}
# {#                            <div>#}
# {#                                Opening holding shape for back. (later is better) <br>#}
# {#                                <input data-row-index={index} type="radio" name="" id=""> piked down#}
# {#                                <input data-row-index={index} type="radio" name="" id=""> tucked down (adds 0.1 to deduction)#}
# {##}
# {#                                <input data-row-index={index} type="radio" name="horz" id=""> bet 12 & 3 o'clock 0.2#}
# {#                                <input data-row-index={index} type="radio" name="horz" id=""> bet 3 & 4:30 o'clock 0.1#}
# {#                            </div>#}
# {#                            <div>#}
# {#                                End of twist <br>#}
# {#                                <input data-row-index={index} type="checkbox" name="" id=""> not finished twist at 3 o'clock 0.1#}
# {#                            </div>#}
# {#                            <div>#}
# {#                                Arms to stop twist (baraini/full/half outs) <br>#}
# {#                                <input data-row-index={index} type="checkbox" name="" id=""> arms >45&deg; 0.1#}
# {#                            </div>#}
# {##}
# {#                            <div>#}
# {#                                Arms to stop twist (>full twist)#}
# {#                                <input data-row-index={index} type="checkbox" name="" id=""> arms >90&deg; 0.1#}
# {#                            </div>#}
# {#                        </div>#}