## Database setup

create database kpub;
use kpub;

CREATE TABLE `pubs` (
  id              integer       not null unique,
  bibcode         varchar(32)   not null unique,
  year            int           not null,
  month           int           not null,
  date            varchar(10)   not null,
  mission         varchar(64)   default '',
  science         varchar(64)   default '',
  instruments     varchar(255)  default '',
  archive         tinyint(1)    default 0,
  metrics         json          default '',
  delflag         tinyint(1)    default 0,
  lastmod         timestamp     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE USER 'kpub'@'localhost' IDENTIFIED BY '[PASSWORD]';
GRANT select, update, insert, delete ON kpub.* TO 'kpub'@'[SERVER]' indentified by '[PASSWORD]';


## Installation on Keck server

ssh user@server
cd ~/bin
git clone https://github.com/KeckObservatory kpub
cd kpub
/usr/local/anaconda/bin/conda env create -f environment.yaml


