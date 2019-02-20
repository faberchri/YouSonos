import React from "react";
import {searchResults, searchTracks, Track} from "./api";
import {Subject, timer} from "rxjs";
import {debounce} from "rxjs/operators";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import SearchResultList from "./SearchResultList";
import SearchInputField from "./SearchInputField";

interface State {
    searchString: string;
    indicateError: boolean,
    indicateSearchRunning: boolean
}

const styles = (theme: Theme) => createStyles({
    root: {
        display: 'flex',
        flexFlow: 'column',
    }
});

interface Props extends WithStyles<typeof styles> {
}

class SearchControl extends React.Component<Props, State> {

    subject = new Subject<string>();

    constructor(props: Props) {
        super(props);
        this.state = SearchControl.getInitialState();
        this.subject
            .pipe(debounce(() => timer(500)))
            .subscribe((url) => searchTracks(url));
    }

    static getInitialState(): State {
        return {
            searchString: '',
            indicateError: false,
            indicateSearchRunning: false
        };
    }

    componentDidMount() {
        searchResults(this.setSearchResults);
    }

    setSearchResults = (searchResults: Track[]) =>{
        this.setState({
            searchString: this.state.searchString,
            indicateError: searchResults.length === 0,
            indicateSearchRunning: false
        });
    };

    runSearch = (searchString: string) => {
        if (searchString.length === 0) {
            this.cancelSearch();
        } else {
            this.setState({
                searchString: searchString,
                indicateError: false,
                indicateSearchRunning: true
            });
            this.subject.next(searchString);
        }
    };

    cancelSearch = () => {
        this.setState(SearchControl.getInitialState());
        // TODO send cancel to backend
    };

    render() {

        const {classes} = this.props;

        return (
            <div className={classes.root} >
                <SearchInputField
                    searchString={this.state.searchString}
                    onValueChange={this.runSearch}
                    onFieldReset={this.cancelSearch}
                    indicateError={this.state.indicateError}
                    indicateSearchRunning={this.state.indicateSearchRunning} />
                <SearchResultList/>
            </div>
        );
    }
}

export default withStyles(styles)(SearchControl);
