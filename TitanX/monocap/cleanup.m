

dirsToClean = {
    'VID_20161106_113020_blur_dark_0.6'
    'VID_20161106_113151_blur_dark_0.6'
    'VID_20161106_113357_practice_blur_dark_0.6'
    'VID_20161106_113534_blur_dark_0.6'
    'VID_20161106_113827_blur_dark_0.6'
    'VID_20161106_113946_blur_dark_0.6'
    'VID_20161106_114059_blur_dark_0.6'
    'VID_20161106_115622_practice_blur_dark_0.6'
};
%%
for jj = 1:numel(dirsToClean)

	datapath = strcat('/home/titan/paul_connolly/videos/', dirsToClean(jj));
    datapath = char(datapath)

	filelist = dir([datapath '/frame*.png']);
	imagelist = {filelist.name};
	nImg = length(imagelist);
	image = [];
	for i = 1:nImg
	    image = cat(4,image,imread(sprintf('%s/%s',datapath,imagelist{i})));
	end
    %% 
	disp('Got All Images')
    %% 


	load(strcat(datapath, filesep, 'preds_2d.mat'))
	load(strcat(datapath, filesep, 'preds_3d.mat'))

	disp('Saving data')
	for i = 1:nImg
	    % Set up the path info because matlab is hella awkward
	    filenamePath = strcat(datapath, filesep, 'monocap_preds_2d.h5');
	    frameNum = imagelist{i}(end-7:end-4);
	    datasetPath = sprintf('/monocap_preds_2d/%s',frameNum);
	    % Create and write the data to the hdf5 container as preds_2d/0000
	    h5create(filenamePath, datasetPath, [2 16]);
	    h5write(filenamePath, datasetPath, preds_2d(:,:,i));
	end

	movefile(strcat(datapath, filesep, 'preds_2d.mat'), strcat(datapath, filesep, 'monocap_preds_2d.mat'))
	movefile(strcat(datapath, filesep, 'preds_3d.mat'), strcat(datapath, filesep, 'monocap_preds_3d.mat'))

	disp(sprintf('Finished %d of %d', jj, numel(dirsToClean)))

end

