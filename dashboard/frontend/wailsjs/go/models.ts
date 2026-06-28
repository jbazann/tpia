export namespace main {
	
	export class Rule {
	    id: number;
	    rule_name: string;
	    priority: number;
	    target_agent: string;
	    action_type: string;
	    payload: string;
	    is_active: boolean;
	
	    static createFrom(source: any = {}) {
	        return new Rule(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.rule_name = source["rule_name"];
	        this.priority = source["priority"];
	        this.target_agent = source["target_agent"];
	        this.action_type = source["action_type"];
	        this.payload = source["payload"];
	        this.is_active = source["is_active"];
	    }
	}

}

