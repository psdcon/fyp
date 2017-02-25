skill_deductions = {
    'tuck jump, pike jump, straddle jump,': ['arms', 'legs', 'body', 'angle_with_horizontal', 'opening_shape_jumps'],
    'seat drop': ['arms', 'legs', 'body'],
    'Swivel Hips/Seat Half Twist to Seat Drop': ['arms', 'legs', 'body', 'twist_timing'],
    'Half Twist to Feet (from seat)': ['arms', 'legs', 'body', 'twist_timing'],
    'front drop, back drop': ['arms', 'legs', 'body'],  # "windmilling"
    'to feet (from front), to feet (from back)': ['arms', 'legs', 'body'],
    'half twist jump, full twist jump': ['arms', 'legs', 'body', 'twist_timing'],
    'front/back somi': ['arms', 'legs', 'body', 'opening_timing_somi', 'opening_holding_shape_feet_front'],
}

judging_rows_html = {

    'arms': """
<div class="js-deduction_category clearfix">
    Arms
    <span class="pull-right">
        <label><input data-row-index={index} type="checkbox" name="arms" value="0.1"> 0.1 Bent elbows</label>
    </span>
</div>""",

    'legs': """
<div class="js-deduction_category clearfix" title="Bent knees, toes not pointed, legs note">
    Legs
    <span class="pull-right">
        <label><input data-row-index={index} type="checkbox" name="legs_knees" value="0.1"> 0.1 Knees</label>
        <label><input data-row-index={index} type="checkbox" name="legs_toes" value="0.1"> 0.1 Toes</label>
        <label><input data-row-index={index} type="checkbox" name="legs_apart" value="0.1"> 0.1 Apart</label>
    </span>
</div>""",

    # <!-- tighness of shape/dished/angle of hips(pikey) -->
    'body': """
<div class="js-deduction_category clearfix">
    Body
    <span class="pull-right">
        <label><input data-row-index={index} type="radio" name="body-{index}" value="0.1"> 0.1 Loose</label>
        <label><input data-row-index={index} type="radio" name="body-{index}" value="0.2"> 0.2 Very loose</label>
    </span>
</div>""",

    'angle_with_horizontal': """
<div class="js-deduction_category clearfix">
    Legs with Horizontal
    <span class="pull-right">
        <label><input data-row-index={index} type="radio" name="legs_horz-{index}" value="0.1"> 0.1 >65&deg; <90&deg;</label>
        <label><input data-row-index={index} type="radio" name="legs_horz-{index}" value="0.2"> 0.2 >45&deg; <65&deg;</label>
    </span>
</div>""",

    'opening_shape_jumps': """
<div class="js-deduction_category clearfix">
    Opening (shape jumps) TODO fix
    <span class="pull-right">
        <label><input data-row-index={index} type="checkbox" name="line_out" value="0.1"> 0.1 Line out</label>
    </span>
</div>""",

    'opening_timing_somi': """
<div class="js-deduction_category clearfix">
    Opening timing (somi) for feet/front landing (cody)/back landing
    <span class="pull-right">
        <label><input data-row-index={index} type="radio" name="opening_timing-{index}" value="0.1"> 0.1 bet 1 &amp; 2 o'clock</label>
        <label><input data-row-index={index} type="radio" name="opening_timing-{index}" value="0.2"> 0.2 bet 2 &amp; 3 o'clock</label>
        <label><input data-row-index={index} type="radio" name="opening_timing-{index}" value="0.3"> 0.3 after 3/no opening</label>
    </span>
</div>""",

    'opening_holding_shape_feet_front': """
<div class="js-deduction_category clearfix">
    Opening holding shape for feet or front. (later is better)
    Person
    <label><input data-row-index={index} type="radio" name="opening_holding_front_shape-{index}" value="pik"> piked down</label>
    <label><input data-row-index={index} type="radio" name="opening_holding_front_shape-{index}" value="tuc"> tucked down</label>

    <span class="pull-right">
        <label><input data-row-index={index} type="radio" name="opening_holding_front_deduction-{index}" value="0.2"> 0.2 bet 12 &amp; 2 o'clock</label>
        <label><input data-row-index={index} type="radio" name="opening_holding_front_deduction-{index}" value="0.1"> 0.1 bet 2 &amp; 3 o'clock</label>
    </span>
</div>""",

    'opening_holding_shape_back': """
<div class="js-deduction_category clearfix">
    Opening holding shape for back. (later is better)
    <span class="pull-right">
        <label><input data-row-index={index} type="radio" name="opening_holding_back_shape-{index}" value="pik"> piked down</label>
        <label><input data-row-index={index} type="radio" name="opening_holding_back_shape-{index}" value="tuc"> tucked down (adds 0.1 to deduction)</label>

        <label><input data-row-index={index} type="radio" name="opening_holding_back_deduction-{index}" value="0.2"> 0.2 bet 12 &amp; 3 o'clock</label>
        <label><input data-row-index={index} type="radio" name="opening_holding_back_deduction-{index}" value="0.1"> 0.1 bet 3 &amp; 4:30 o'clock</label>
    </span>
</div>""",

    'twist_timing': """
<div class="js-deduction_category clearfix">
    Twist Timing
    <span class="pull-right">
        <label><input data-row-index={index} type="checkbox" name="" value="0.1"> 0.1 twist at 3</label>
    </span>
</div>""",

    'twist_arms_half_full': """
<div class="js-deduction_category clearfix">
    Arms to stop twist (baraini/full/half outs)
    <span class="pull-right">
        <label><input data-row-index={index} type="checkbox" name="" value="0.1"> 0.1 arms >45&deg;</label>
    </span>
</div>""",

    'twist_arms_over_full': """
<div class="js-deduction_category clearfix">
    Arms to stop twist (>full twist)
    <span class="pull-right">
        <label><input data-row-index={index} type="checkbox" name="" value="0.1"> 0.1 arms >90&deg;</label>
    <span class="pull-right">
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