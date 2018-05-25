import scrapy.commands.crawl as crawl
from scrapy.exceptions import UsageError
from scrapy.commands import ScrapyCommand
import config
import filter

class Command(crawl.Command):
    def syntax(self):
        return "<pantip_tag_name> <database_name>"

    def short_desc(self):
        return "Crawl pantip"
        
    def long_desc(self):
        return "Crawl pantip data to a MySQL database."
        
    def add_options(self, parser):
        ScrapyCommand.add_options(self, parser)
        parser.add_option("-a", dest="spargs", action="append", default=[], metavar="NAME=VALUE",
                          help="set spider argument (may be repeated)")
        parser.add_option("-o", "--output", metavar="FILE",
                          help="dump scraped items into FILE (use - for stdout)")
        parser.add_option("-t", "--output-format", metavar="FORMAT",
                          help="format to use for dumping items with -o")
                          
        parser.add_option("-p", "--pages", nargs = 2, type="int", dest="pages", default=[],
                          help="set the range of pages you want to crawl")  
        parser.add_option("-f", "--filter", type="str", dest="filter", default="",
                          help='set function name in "filter.py" to filter threads')
                          
    def set_pages(self, pages):
        if len(pages) == 0:
            begin_page = 1
            end_page = 999999
        else:
            begin_page = pages[0]
            end_page = pages[1]
        if begin_page <= 0:
            raise UsageError("The number of begin page must not be less than 1!")
        if begin_page > end_page:
            raise UsageError("The number of end page must not be less than that of begin page!")
        self.settings.set('BEGIN_PAGE', begin_page, priority='cmdline')
        self.settings.set('END_PAGE', end_page, priority='cmdline')

    def run(self, args, opts):
        self.set_pages(opts.pages)
        if opts.filter:
            try:
                opts.filter = eval('filter.' + opts.filter)
            except:
                raise UsageError("Invalid filter function name!")
        self.settings.set("FILTER", opts.filter)
        cfg = config.config()
        if len(args) >= 3:
            raise UsageError("Too many arguments!")
        
        self.settings.set('MYSQL_HOST', cfg.config['MYSQL_HOST'])
        self.settings.set('MYSQL_USER', cfg.config['MYSQL_USER'])
        self.settings.set('MYSQL_PASSWD', cfg.config['MYSQL_PASSWD'])
        self.settings.set('MYSQL_USE_SSL', cfg.config['MYSQL_USE_SSL'])
        self.settings.set('MYSQL_SSL_CHECK_HOSTNAME', cfg.config['MYSQL_SSL_CHECK_HOSTNAME'])
        self.settings.set('MYSQL_SSL_CA_PATH', cfg.config['MYSQL_SSL_CA_PATH'])
        
        
        tbname = cfg.config['DEFAULT_TIEBA']
        if len(args) >= 1:
            tbname = args[0]
        if isinstance(tbname, str):
            tbname = tbname.encode('utf8')
            
        dbname = None    
        for key in cfg.config['MYSQL_DBNAME'].keys():
            if key.encode('utf8') == tbname:
                dbname = cfg.config['MYSQL_DBNAME'][key]
        if len(args) >= 2:
            dbname = args[1]
            cfg.config['MYSQL_DBNAME'][tbname.decode('utf8')] = dbname
        if not dbname:
            raise UsageError("Please input database name!")
            
        self.settings.set('TIEBA_NAME', tbname, priority='cmdline')
        self.settings.set('MYSQL_DBNAME', dbname, priority='cmdline')

        use_ssl = False
        ssl_check_hostname = False

        if cfg.config['MYSQL_USE_SSL'] == 'True':
            use_ssl = True
        
        if cfg.config['MYSQL_SSL_CHECK_HOSTNAME'] == 'False':
            ssl_check_hostname = False
        else: 
            ssl_check_hostname = True
        
        config.init_database(cfg.config['MYSQL_HOST'],\
            cfg.config['MYSQL_USER'], cfg.config['MYSQL_PASSWD'], dbname,\
            use_ssl = use_ssl, ssl_check_hostname = ssl_check_hostname,\
            ssl_ca = cfg.config['MYSQL_SSL_CA_PATH'], spider_type='pantip')

        
        log = config.log(tbname, dbname, self.settings['BEGIN_PAGE'])
        self.settings.set('SIMPLE_LOG', log)
        
        self.crawler_process.crawl('pantip', **opts.spargs)
        self.crawler_process.start()
        
        cfg.save()

        
            
  
