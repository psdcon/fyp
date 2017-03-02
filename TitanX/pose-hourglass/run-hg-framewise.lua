-- Usuage: qlua run-hg-framewise.lua ../../videos/VID_20161106_112900_720x480/

-- Generates heatmaps for frames in a folder 
-- The heatmaps are saved in the hdf5 file 'heatmaps.h5' in the same folder

nClock = os.clock()

require 'paths'
paths.dofile('util.lua')
paths.dofile('img.lua')

local imgdir = arg[1]

model = torch.load('/home/titan/paul_connolly/pose-hourglass/umich-stacked-hourglass.t7')   -- Load pre-trained model

-- Open file for heatmaps
local heatmapsH5Name = paths.concat(imgdir,'hg_heatmaps.h5')
print('Opening ' .. heatmapsH5Name)
local heatmapsFile = hdf5.open(heatmapsH5Name,'w')

-- Open file for 2d pose predictions
local predsH5Name = paths.concat(imgdir,'hg_preds_2d.h5')
print('Opening ' .. predsH5Name)
local predsFile = hdf5.open(predsH5Name,'w')

-- Get all files with name in format 'frame_0000.png'. Save frame number in table
files = {}
frame_nums = {}
file_count = 0
for file in paths.files(imgdir) do
    -- escape regex tokens with % rather than \
    frame_num = file:match('^frame_(%d+)%.png$')
    if frame_num then
        table.insert(files, file)
        table.insert(frame_nums, frame_num)        
        file_count = file_count + 1
    end
end
table.sort(files)

-- Loop to predict
done_count = 0
for i,file in ipairs(files) do
    local name = paths.concat(imgdir,file)
    local img = image.load(name)
    local center = torch.Tensor(2)
    center[1] = img:size(3)/2 -- width
    center[2] = img:size(2)/2 -- height
    local scale = img:size(2) / 200--340 -- integer division
    local inp = crop(img,center,scale,0,256) -- crop(img, center, scale, rot, res)
    
    -- Create the prediction heatmap
    local out = model:forward(inp:view(1,3,256,256):cuda())
    local hm = out[2][1]:float()
    hm[hm:lt(0)] = 0
    
    -- Generate pose point predictions from the heatmap
    local preds_hm, preds_img = getPreds(hm, center, scale)
    
    -- Get current frames frame number
    local frame_num = frame_nums[i]
    
    -- Save each heatmap to hg_heatmaps/0000
    heatmapsFile:write('hg_heatmaps/'..frame_num, hm)
    -- Save each prediction in hg_preds_2d/0000
    predsFile:write('hg_preds_2d/'..frame_num, preds_img[1])
    
    -- Save each heatmap in its own file
    -- local predsH5Name = name:gsub(ext,'h5')
    -- local predFileFrame = hdf5.open(predsH5Name,'w')
    -- predFileFrame:write('heatmap',hm)
    -- predFileFrame:close()
    
    -- Save predicition image
    -- if false then
    --     preds_hm:mul(4)
    --     local displayImg = drawOutput(inp, hm, preds_hm[1])
    --     posed_image_filepath = paths.concat(imgdir,'posed_'..file)
    --     image.save(posed_image_filepath, displayImg)
    --     -- w = image.display{image=displayImg, win=w}
    --     -- sys.sleep(1)
    -- end

    -- Print progress
    done_count = done_count + 1
    print(file .. ', ' .. done_count  .. ' of '..file_count .. ', ' 
        .. string.format('%.1f', (done_count/file_count)*100) .. '%')
end

print('Closing ' .. heatmapsH5Name)
heatmapsFile:close()
print('Closing ' .. predsH5Name)
predsFile:close()

print('Execution took: ' .. os.clock()-nClock .. 's')

-- Script always end with a seg fault. Don't know/understand why