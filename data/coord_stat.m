figure;
format long g;
fid = fopen('vbr1', 'rt');
C = textscan(fid, '%f %f %f %s', 'delimiter', ',' , 'EndOfLine', '\n');
data = [C{1} C{2} C{3}];
fclose(fid);
m = data(:,1:3);
m(any(m(:,2)== 6,2),:)=[];
m(any(m(:,2)== 7,2),:)=[];
m(any(m(:,2)== 8,2),:)=[];
m(:,1) = 1:500;
i = m(:,2:3);
mean = [sum(m(:,3))/size(m,1) 30*sum(m(:,3))/size(m,1)/1000];
m(:,2) = mean(1);
subplot(2,1,1)
plot(m(:,1),m(:,3), m(:,1),m(:,2));
ylabel('Frame size (Kb)')
axis([1 500 0 500]);
box on;
title(sprintf('VBR with mean rate = %f Mbps', mean(2)));
legend('Frame size','Mean size','Location','north');
legend boxoff;

fid = fopen('cbr1', 'rt');
C = textscan(fid, '%f %f %f %s', 'delimiter', ',' , 'EndOfLine', '\n');
data = [C{1} C{2} C{3}];
fclose(fid);
m = data(:,1:3);
m(any(m(:,2)== 6,2),:)=[];
m(any(m(:,2)== 7,2),:)=[];
m(any(m(:,2)== 8,2),:)=[];
m(:,1) = 1:500;
j = m(:,2:3);
mean = [sum(m(:,3))/size(m,1) 30*sum(m(:,3))/size(m,1)/1000];
m(:,2) = mean(1);
subplot(2,1,2)
plot(m(:,1),m(:,3), m(:,1),m(:,2));
xlabel('Frame number')
ylabel('Frame size (Kb)')
axis([1 500 0 500]);
box on;
title(sprintf('CBR with mean rate = %f Mbps', mean(2)));
legend('Frame size','Mean size','Location','north');
legend boxoff;

fname = 'video1';
fid = fopen(fname,'w');
fprintf(fid, '%d %05.3f %d %05.3f\n' ,transpose([i j]));
fclose(fid);

figure;
fid = fopen('vbr2', 'rt');
C = textscan(fid, '%f %f %f %s', 'delimiter', ',' , 'EndOfLine', '\n');
data = [C{1} C{2} C{3}];
fclose(fid);
m = data(:,1:3);
m(any(m(:,2)== 6,2),:)=[];
m(any(m(:,2)== 7,2),:)=[];
m(any(m(:,2)== 8,2),:)=[];
m(:,1) = 1:500;
i = m(:,2:3);
mean = [sum(m(:,3))/size(m,1) 30*sum(m(:,3))/size(m,1)/1000];
m(:,2) = mean(1);
subplot(2,1,1)
plot(m(:,1),m(:,3), m(:,1),m(:,2));
ylabel('Frame size (Kb)')
axis([1 500 0 500]);
box on;
title(sprintf('VBR with mean rate = %f Mbps', mean(2)));
legend('Frame size','Mean size','Location','north');
legend boxoff;

fid = fopen('cbr2', 'rt');
C = textscan(fid, '%f %f %f %s', 'delimiter', ',' , 'EndOfLine', '\n');
data = [C{1} C{2} C{3}];
fclose(fid);
m = data(:,1:3);
m(any(m(:,2)== 6,2),:)=[];
m(any(m(:,2)== 7,2),:)=[];
m(any(m(:,2)== 8,2),:)=[];
m(:,1) = 1:500;
j = m(:,2:3);
mean = [sum(m(:,3))/size(m,1) 30*sum(m(:,3))/size(m,1)/1000];
m(:,2) = mean(1);
subplot(2,1,2)
plot(m(:,1),m(:,3), m(:,1),m(:,2));
xlabel('Frame number')
ylabel('Frame size (Kb)')
axis([1 500 0 500]);
box on;
title(sprintf('CBR with mean rate = %f Mbps', mean(2)));
legend('Frame size','Mean size','Location','north');
legend boxoff;

fname = 'video2';
fid = fopen(fname,'w');
fprintf(fid, '%d %5.3f %d %5.3f\n',transpose([i j]));
fclose(fid);

figure;
fid = fopen('vbr3', 'rt');
C = textscan(fid, '%f %f %f %s', 'delimiter', ',' , 'EndOfLine', '\n');
data = [C{1} C{2} C{3}];
fclose(fid);
m = data(:,1:3);
m(any(m(:,2)== 6,2),:)=[];
m(any(m(:,2)== 7,2),:)=[];
m(any(m(:,2)== 8,2),:)=[];
m(:,1) = 1:500;
i = m(:,2:3);
mean = [sum(m(:,3))/size(m,1) 30*sum(m(:,3))/size(m,1)/1000];
m(:,2) = mean(1);
subplot(2,1,1)
plot(m(:,1),m(:,3), m(:,1),m(:,2));
ylabel('Frame size (Kb)')
axis([1 500 0 500]);
box on;
title(sprintf('VBR with mean rate = %f Mbps', mean(2)));
legend('Frame size','Mean size','Location','north');
legend boxoff;

fid = fopen('cbr3', 'rt');
C = textscan(fid, '%f %f %f %s', 'delimiter', ',' , 'EndOfLine', '\n');
data = [C{1} C{2} C{3}];
fclose(fid);
m = data(:,1:3);
m(any(m(:,2)== 6,2),:)=[];
m(any(m(:,2)== 7,2),:)=[];
m(any(m(:,2)== 8,2),:)=[];
m(:,1) = 1:500;
j = m(:,2:3);
mean = [sum(m(:,3))/size(m,1) 30*sum(m(:,3))/size(m,1)/1000];
m(:,2) = mean(1);
subplot(2,1,2)
plot(m(:,1),m(:,3), m(:,1),m(:,2));
xlabel('Frame number')
ylabel('Frame size (Kb)')
axis([1 500 0 500]);
box on;
title(sprintf('CBR with mean rate = %f Mbps', mean(2)));
legend('Frame size','Mean size','Location','north');
legend boxoff;

fname = 'video3';
fid = fopen(fname,'w');
fprintf(fid, '%d %5.3f %d %5.3f\n',transpose([i j]));
fclose(fid);
