-- Generate heatmaps for all images in a folder
-- The heatmaps are saved as hdf5 files in the same folder
-- routine: th run-hg.lua FolderName ImageFilenameExtension
-- example: th run-hg.lua ../data/tennis jpg

require 'paths'
require("pl")
require("image")
local video = assert(require("libvideo_decoder"))
paths.dofile('util.lua')
paths.dofile('img.lua')

-- local imgdir = arg[1]
-- local ext = arg[2]

-- Options ---------------------------------------------------------------------
opt = lapp([[
-v, --videoPath    (default '')    path to video file
]])


model = torch.load('umich-stacked-hourglass.t7')   -- Load pre-trained model


-- load a video and extract frame dimensions
local status, height, width, length, fps = video.init(opt.videoPath)
if not status then
    error("No video")
else
    print('Video statistics: '..height..'x'..width..' ('..(length or 'unknown')..' frames)')
end

-- construct tensor
local img = torch.ByteTensor(3, height, width)

-- loop through frames
local timer = torch.Timer()
for i = 0, nb_frames do
    video.frame_rgb(img)

    local center = torch.Tensor(2)
    center[1] = img:size(3)/2
    center[2] = img:size(2)/2
    local scale = img:size(2) / 200
    local savefile = name:gsub(ext,'h5')

    local inp = crop(img,center,scale,0,256)
    local out = model:forward(inp:view(1,3,256,256):cuda())
    local hm = out[2][1]:float()
    hm[hm:lt(0)] = 0

    local predFile = hdf5.open(savefile,'w')
    predFile:write('heatmap',hm)
    predFile:close()

    print(savefile)

end

print('Time: ', timer:time().real/nb_frames)

-- free variables and close the video
video.exit()
