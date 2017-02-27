-- Usuage: qlua run-hg-framewise.lua ../../videos/VID_20161106_112900_720x480/ png

-- Generate heatmaps for all images in a folder 
-- The heatmaps are saved as hdf5 files in the same folder
-- routine: th run-hg.lua FolderName ImageFilenameExtension
-- example: th run-hg.lua ../data/tennis jpg 
nClock = os.clock()

require 'paths'
paths.dofile('util.lua')
paths.dofile('img.lua')

local imgdir = arg[1]
local ext = arg[2]

model = torch.load('umich-stacked-hourglass.t7')   -- Load pre-trained model

local savefile = paths.concat(imgdir,'preds.h5')
local predFile = hdf5.open(savefile,'w')
print(savefile)

file_count = 0
for file in paths.files(imgdir) do
    if file:find(ext .. '$') then
        file_count = file_count + 1
    end
end

-- Sort files so that when playing back the predictions, its not random
files = {}
for file in paths.files(imgdir) do table.insert(files, file) end
table.sort(files)

done_count = 0
for i,file in ipairs(files) do
-- for file in paths.files(imgdir) do
    if file:find(ext .. '$') then
        local name = paths.concat(imgdir,file)
        local img = image.load(name)
        local center = torch.Tensor(2)
        center[1] = img:size(3)/2 -- width
        center[2] = img:size(2)/2 -- height
        local scale = img:size(2) / 200--340 -- integer division
        -- print(scale)
        local inp = crop(img,center,scale,0,256) -- crop(img, center, scale, rot, res)
        
        -- Create the prediction heatmap
        local out = model:forward(inp:view(1,3,256,256):cuda())
        local hm = out[2][1]:float()
        hm[hm:lt(0)] = 0
        
        -- Generate pose point predictions from the heatmap
        local preds_hm, preds_img = getPreds(hm, center, scale)
        
        -- Extract the current frame number as a string from the filename
        fn_start = file:len()-7
        fn_end = file:len()-4
        frame_num = file:sub(fn_start, fn_end)
        
        -- Save each prediction to an array
        -- predFile:write('heatmap',hm)
        predFile:write('preds/'..frame_num, preds_img[1])
        
        -- Save each heatmap in its own file
        local savefile = name:gsub(ext,'h5')
        local predFileFrame = hdf5.open(savefile,'w')
        predFileFrame:write('heatmap',hm)
        predFileFrame:close()
        
        -- Display stuff
        if true then
            preds_hm:mul(4)
            local displayImg = drawOutput(inp, hm, preds_hm[1])
            posed_image_filepath = paths.concat(imgdir,"posed_"..file)
            image.save(posed_image_filepath, displayImg)
            -- w = image.display{image=displayImg, win=w}
            -- sys.sleep(1)
        end

        -- Print progress
        done_count = done_count + 1
        print("Frame " .. frame_num .. ". " 
            .. done_count  .. " of "..file_count .. " = " .. 
            string.format("%.1f", (done_count/file_count)*100) .. "%")

    end
end

print(savefile)

print("Execution took: " .. os.clock()-nClock)

predFile:close()
