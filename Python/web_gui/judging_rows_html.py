"""' 16'
'Back Drop y'
'Back S/S to Seat y'
'Back S/S y'
'Barani y'
'Broken 24'
'Crash Dive y'
'Front Drop y'
'Front S/S y'
'Full Twist Jump y'
'Half Twist Jump y'
'Half Twist to Feet from back y'
'Half Twist to Feet (from seat y'
'Half Twist to Seat Drop y'
'In/Out Bounce y'
'Lazy Back y'
'Pike Jump y'
'Seat Drop y'
'Straddle Jump y'
'Swivel Hips/Seat Half Twist to Seat Drop y'
'To Feet (from back y'
'To Feet (from front y'
'To Feet (from seat y'
'Tuck Jump y'

------------

"" blank
"Back Drop" y
"Back Half"y
"Back S/S" y
"Back S/S to Seat"y
"Barani" y
"Barani Ball Out" y
"Broken"
"Cody" y
"Crash Dive" y
"Front Drop" y
"Front S/S" y
"Full Back" y
"Full Front" y
"Full Twist Jump" y
"Half Twist Jump" y
"Half Twist to Feet from Back" y
"Half Twist to Feet from Seat" y
"Half Twist to Seat Drop" y
"In/Out Bounce" y
"Landing"  y
"Lazy Back" y
"Pike Jump" y
"Rudolph / Rudi" y
"Seat Drop" y
"Straddle Jump" y
"Swivel Hips/Seat Half Twist to Seat Drop" y
"To Feet from Back" y
"To Feet from Front" y
"To Feet from Seat" y
"Tuck Jump" y
"""

deduction_categories_per_skill = {
    'tuck jump': [  # no angle with horizontal deduction
        'arms',
        'legs',
        'body',
        'opening_shape_jumps'
    ],
    'pike jump, straddle jump,': [
        'arms',
        'legs',
        'body',
        'angle_with_horizontal',
        'opening_shape_jumps'
    ],
    'Full Back, Back Half, Barani, Barani Ball Out, full front': [
        'arms_twist_half_full',
        'legs',
        'body',
        'opening_timing_feet_front',
        'after_opening_feet_front',
        'twist_timing',
    ],
    'Rudolph / Rudi': [
        'arms_twist_over_full',
        'legs',
        'body',
        'opening_timing_feet_front',
        'after_opening_feet_front',
        'twist_timing',
    ],
    'seat drop, To Feet from seat, to feet from front, to feet from back, front drop, back drop, Half Twist to Feet from back, Half Twist to Seat Drop, Swivel Hips/Seat Half Twist to Seat Drop, Half Twist to Feet from seat, half twist jump, full twist jump': [
        'arms',
        'legs',
        'body'  # shouldn't show somi shapes
    ],
    'Back S/S, Back S/S to Seat, lazy back, Front S/S, Cody, lazy back': [
        'arms',
        'legs',
        'body',  # should show somersault shape
        'opening_timing_feet_front',  # wouldn't deduct for straight
        'after_opening_feet_front'
    ],
    'crash dive': [
        'arms',
        'legs',
        'body',
        'opening_timing_back',
        'after_opening_back'
    ],
    'in/out bounce': [
        'out_bounce',
    ],
    'landing': [
        'landing',
    ],
    'broken': [
        'broken',
    ]

}
