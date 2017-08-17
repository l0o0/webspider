# -*- coding=utf-8 -*-
#!/usr/bin/env python

# Detect new project in genebang project pool, 
# send a notification when new project is found.

import os
import requests
import requests.packages.urllib3
import time
import logging

from lxml import etree
from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

requests.packages.urllib3.disable_warnings()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='access.log',
                    filemode='w')
access_logger = logging.getLogger('access')
add_logger = logging.getLogger('add')

POOL_INDEX = "https://www.genebang.com/project-pool/index"
PROJECT_URL = "https://www.genebang.com/project-pool/detail/"   # need project id
DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath('.'), 'data.sqlite')


# Table class for Project
Base = declarative_base()


class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    url = Column(String(20))


engine = create_engine(DATABASE_URI)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)



def sendcloud(to, query, subject='New Project'):
    url = "http://api.sendcloud.net/apiv2/mail/send"
    project_list = ''    

    for item in query:
        project_list += "<li><a href=%s%s>%s</a></li>" % (PROJECT_URL, item[0], item[1])

    html = "<p>New projects!</p>\n<ul>%s</ul>" % project_list
    #txt = render_template(template + '.txt', **kwargs)
    params = {"apiUser": os.getenv('apiUser'),
            "apiKey": os.getenv('apiKey'),
            "from":"PersonalAssist<l0o0@my.com>",
            "to": to,
            "fromName": "l0o0l",
            "subject": subject,
            "html": html,
            }
    r = requests.post(url, data=params)
    return r



def auto_detect(sleep=300):
    '''
    Detect new projects by search the project pool index page every 300s(by default).
    '''
    while True:
        page = requests.get(POOL_INDEX, verify=False).text
        html = etree.HTML(page)
        session = DBSession()
        tmp_project = []
        for item in html.xpath('//div[@class="project-detail-name"]/a'):
            #access_logger.info(' : '.join(item.values()).encode('utf-8'))
            url, blank, name = item.values()
            url = os.path.basename(url)
            project = session.query(Project).filter(Project.url == url).first()
            if not project:
                project = Project()
                project.url = url
                project.name = name
                session.add(project)
                session.commit()
                session.close()
                tmp_project.append((url, name))
                add_logger.info('add : %s:%s' % (url,name.encode('utf-8')))
        if tmp_project:
            response = sendcloud('linxzh1989@qq.com', tmp_project) 
            access_logger.info(response.text)
        access_logger.info('-' * 5 )

        time.sleep(sleep)


if __name__ == "__main__":
    auto_detect(sleep=600)
