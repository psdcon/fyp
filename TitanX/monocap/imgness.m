clear 

% This script outputs images for folders where they've already been posed.
dirsToImg = {
% 'VID_20161106_115931_blur_dark_0.6'
% 'VID_20161106_120056_blur_dark_0.6'
% 'VID_20161106_120437_blur_dark_0.6'
% 'VID_20161106_120612_blur_dark_0.6'
% 'VID_20161106_120722_blur_dark_0.6'
% 'VID_20161106_120832_blur_dark_0.6'
% 'VID_20161106_121333_blur_dark_0.6'
% 'VID_20161106_121456_blur_dark_0.6'
% 'VID_20161106_121735_blur_dark_0.6'
'VID_20161106_121903_blur_dark_0.6'
};

startup

% load dictionary learned from Human3.6M or CMU

dict = load('dict/poseDict-all-K128'); % a general pose dict
dictDataset = 'hm36m';
% dict = load('dict/tennis_forehand.mat'); % a motion-specific dict
% dictDataset = 'cmu';

% convert dictionary format
% because the joint order in MPII is different from that in Human3.6M
dict = getMPIIdict(dict,dictDataset);
numKp = length(dict.skel.tree);


for jj = 1:numel(dirsToImg)
    
    datapath = strcat('/home/titan/paul_connolly/videos/', dirsToImg(jj));
    datapath = char(datapath)
    
    load(strcat(datapath, filesep, 'monocap_preds_2d.mat'))
	load(strcat(datapath, filesep, 'monocap_preds_3d.mat'))

    % Images
    filelist = dir([datapath '/frame*.png']);
    imagelist = {filelist.name};
    nImg = length(imagelist);
    image = [];
    for i = 1:nImg
        image = cat(4,image,imread(sprintf('%s/%s',datapath,imagelist{i})));
    end
    disp('Got All Images')


    % Heatmaps
    heatmap = [];
    for i = 1:nImg
        frameNum = imagelist{i}(end-7:end-4);
        hm = h5read(sprintf('%s/hg_heatmaps.h5', datapath), sprintf('/hg_heatmaps/%s', frameNum));
        heatmap = cat(4,heatmap,permute(hm,[2,1,3]));
    end
    disp('Got All Heatmaps')
    

    % Gen Images
    disp('Saving images')
    nPlot = 4;
    thisFig = figure('position',[300 300 200*nPlot 200]);

    for i = 1:nImg

        clf

        subplot(1,nPlot,1);
        imshow(image(:,:,:,i));
    %
        subplot(1,nPlot,2);
        imagesc(mat2gray(sum(heatmap(:,:,:,i),3)));
        axis equal off

        subplot(1,nPlot,3);
        imshow(image(:,:,:,i));
    %     hold on;
        vis2Dskel(preds_2d(:,:,i),dict.skel);

        subplot(1,nPlot,4);
        vis3Dskel(preds_3d(:,:,i),dict.skel,'viewpoint',[-45 0]);

    %         pause(0.01)
        smoothed_pose_plot_filename = strcat(datapath, filesep, 'smoothed_pose_', imagelist(i));
        saveas(thisFig, smoothed_pose_plot_filename{1})

    end
    
end